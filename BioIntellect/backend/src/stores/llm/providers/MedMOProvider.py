import gc
import os
import time
from importlib import import_module
from typing import Any, Optional

import torch
from transformers import AutoProcessor

from ..LLMInterface import LLMInterface
from ..LLMEnums import MedMOEnums
from src.observability.logger import get_logger


class MedMOProvider(LLMInterface):

    @staticmethod
    def _resolve_qwen_model_class():
        candidates = [
            ("transformers.models.qwen3_vl.modeling_qwen3_vl", "Qwen3VLForConditionalGeneration"),
            ("transformers.models.qwen2_5_vl.modeling_qwen2_5_vl", "Qwen2_5_VLForConditionalGeneration"),
            ("transformers.models.qwen2_vl.modeling_qwen2_vl", "Qwen2VLForConditionalGeneration"),
        ]

        for module_name, class_name in candidates:
            try:
                module = import_module(module_name)
                model_class = getattr(module, class_name, None)
                if model_class is not None:
                    return model_class
            except Exception:
                continue
        return None

    @staticmethod
    def is_runtime_available() -> bool:
        try:
            from importlib.util import find_spec

            return (
                MedMOProvider._resolve_qwen_model_class() is not None
                and find_spec("qwen_vl_utils") is not None
            )
        except Exception:
            return False

    @staticmethod
    def _free_gpu_memory() -> None:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def __init__(self, model_path: str, default_input_max_characters: int = 6000,
                 default_output_max_tokens: int = 1024, default_temp: float = 0.3,
                 offload_folder: str = "./offload", force_cpu_only: bool = False):
        self.model_path = model_path
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.offload_folder = offload_folder
        self.force_cpu_only = force_cpu_only
        self.Enums = MedMOEnums
        self.generation_model_id = model_path
        self.embedding_model_id = None
        self.embedding_size = None
        self.model: Any = None
        self.processor: Any = None

        self.logger = get_logger("provider.MedMOProvider")
        self.logger.info("Loading MedMO model from: %s", self.model_path)

        if not self.is_runtime_available():
            raise ImportError(
                "MedMO runtime dependencies are missing. Required: "
                "a supported Qwen-VL class (qwen3/qwen2.5/qwen2) and qwen_vl_utils"
            )
        qwen_model_class = self._resolve_qwen_model_class()

        os.makedirs(self.offload_folder, exist_ok=True)

        has_accelerate = False
        try:
            import accelerate  # noqa: F401
            has_accelerate = True
        except ImportError:
            self.logger.warning("accelerate not installed — device_map disabled")

        load_strategies: list[tuple[str, dict]] = []
        if not self.force_cpu_only:
            try:
                from transformers import BitsAndBytesConfig
                import bitsandbytes  # noqa: F401
                quant_kwargs: dict = {
                    "low_cpu_mem_usage": True,
                    "offload_folder": self.offload_folder,
                    "trust_remote_code": True,
                    "quantization_config": BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    ),
                }
                if has_accelerate:
                    quant_kwargs["device_map"] = "auto"
                load_strategies.append(("4bit", quant_kwargs))
            except ImportError:
                pass

            fp16_kwargs: dict = {
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
                "offload_folder": self.offload_folder,
                "trust_remote_code": True,
            }
            if has_accelerate:
                fp16_kwargs["device_map"] = "auto"
            load_strategies.append(("float16", fp16_kwargs))

        load_strategies.append(("float32-cpu", {
            "torch_dtype": torch.float32,
            "low_cpu_mem_usage": True,
            "offload_folder": self.offload_folder,
            "trust_remote_code": True,
        }))

        load_started = time.perf_counter()
        last_exc: Optional[Exception] = None
        for strategy_name, kwargs in load_strategies:
            try:
                self.logger.info("Attempting to load MedMO with strategy: %s", strategy_name)
                self.model = qwen_model_class.from_pretrained(self.model_path, **kwargs)
                self.processor = AutoProcessor.from_pretrained(self.model_path)
                self.model.eval()
                self.logger.info(
                    "MedMO loaded (strategy=%s, load_s=%.2f)",
                    strategy_name, time.perf_counter() - load_started,
                )
                return
            except Exception as load_exc:
                self.logger.warning("Strategy %s failed: %s", strategy_name, load_exc)
                last_exc = load_exc
                # Release any partially-allocated memory before retrying.
                self.model = None
                self.processor = None
                self._free_gpu_memory()

        raise RuntimeError(
            f"All loading strategies failed for MedMO. Last error: {last_exc}"
        ) from last_exc

    def set_generation_model(self, model_id: str) -> str:
        self.generation_model_id = model_id
        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size: int) -> str:
        raise NotImplementedError(
            "MedMOProvider does not support a separate embedding model. "
            "Use a text-embedding provider (phi_qa/openai/cohere) instead."
        )

    def generate_text(self, prompt: str, chat_history: Optional[list] = None,
                      max_output_tokens: Optional[int] = None, temp: Optional[float] = None,
                      image_path: Optional[Any] = None) -> str:
        if not self.model or not self.processor:
            raise RuntimeError("MedMO model is not loaded.")

        if isinstance(image_path, str):
            image_paths = [image_path] if image_path else []
        else:
            image_paths = [p for p in (image_path or []) if p]

        normalized_history = self._normalize_history(chat_history or [])
        current_turn = self._build_user_turn(prompt=prompt, image_paths=image_paths)
        messages = normalized_history + [current_turn]

        try:
            from qwen_vl_utils import process_vision_info

            gen_started = time.perf_counter()
            text_input = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)

            inputs = self.processor(
                text=[text_input],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to(self.model.device)

            actual_temp = self.default_temp if temp is None else temp
            do_sample = actual_temp is not None and actual_temp > 0
            gen_kwargs: dict = {
                "max_new_tokens": max_output_tokens or self.default_output_max_tokens,
                "do_sample": do_sample,
                "repetition_penalty": 1.15,
            }
            if do_sample:
                gen_kwargs["temperature"] = float(actual_temp)

            with torch.inference_mode():
                generated_ids = self.model.generate(**inputs, **gen_kwargs)

            trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self.processor.batch_decode(
                trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )

            self.logger.info("MedMO generation took %.2fs", time.perf_counter() - gen_started)

            if not output_text or not output_text[0].strip():
                raise RuntimeError("MedMO returned empty output.")

            return output_text[0]

        except RuntimeError:
            raise
        except Exception as e:
            self.logger.error("MedMO generation error: %s", e)
            raise

    def embed_text(self, text: str, document_type: Optional[str] = None) -> list:
        raise NotImplementedError(
            "MedMOProvider does not support text embedding. "
            "Use an embedding-specific provider instead."
        )

    def construct_prompt(self, query: str, role: str) -> dict:
        return {
            "role": role,
            "content": [{"type": "text", "text": query}],
        }

    def process_text(self, text: str) -> str:
        """Truncate and strip the input text. Only use for short user-facing inputs."""
        return text[: self.default_input_max_characters].strip()

    @staticmethod
    def _normalize_history(chat_history: list) -> list:
        normalized: list = []
        for msg in chat_history:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "user")).lower()
            raw_content = msg.get("content")
            text = str(msg.get("message") or (raw_content if isinstance(raw_content, str) else "") or "")

            if role == "system":
                target_role = "system"
            elif role in ("assistant", "chatbot"):
                target_role = "assistant"
            else:
                target_role = "user"

            if isinstance(raw_content, list):
                normalized.append({"role": target_role, "content": raw_content})
            elif text:
                normalized.append({
                    "role": target_role,
                    "content": [{"type": "text", "text": text}],
                })
        return normalized

    def _build_user_turn(self, prompt: str, image_paths: Optional[list] = None) -> dict:
        content: list[dict] = []
        for path in (image_paths or []):
            content.append({"type": "image", "image": path})
        content.append({"type": "text", "text": prompt})
        return {
            "role": MedMOEnums.user.value,
            "content": content,
        }
