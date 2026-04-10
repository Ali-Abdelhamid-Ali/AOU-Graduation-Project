import os
from importlib import import_module

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

        self.logger = get_logger("provider.MedMOProvider")

        self.logger.info(f"Loading MedMO model from: {self.model_path}")
        try:
            if not self.is_runtime_available():
                raise ImportError(
                    "MedMO runtime dependencies are missing. Required: "
                    "a supported Qwen-VL class (qwen3/qwen2.5/qwen2) and qwen_vl_utils"
                )
            qwen_model_class = self._resolve_qwen_model_class()
            if qwen_model_class is None:
                raise ImportError("Failed to resolve a Qwen-VL model class from transformers")

            # Use 4-bit quantization when available for much faster inference
            load_kwargs: dict = {
                "low_cpu_mem_usage": True,
                "offload_folder": self.offload_folder,
                "trust_remote_code": True,
            }
            os.makedirs(self.offload_folder, exist_ok=True)

            quantized = False
            if not self.force_cpu_only:
                try:
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                    )
                    quantized = True
                    self.logger.info("Using 4-bit quantization for faster inference.")
                except ImportError:
                    self.logger.info("bitsandbytes not available — falling back to float16.")
                    load_kwargs["torch_dtype"] = torch.float16

                try:
                    import accelerate  # noqa: F401
                    load_kwargs["device_map"] = "auto"
                except ImportError:
                    self.logger.warning("accelerate not installed — loading MedMO on CPU")
            else:
                load_kwargs["torch_dtype"] = torch.float32

            self.model = qwen_model_class.from_pretrained(self.model_path, **load_kwargs)
            self.processor = AutoProcessor.from_pretrained(self.model_path)
            self.logger.info(
                "MedMO model loaded (force_cpu=%s, quantized=%s).",
                self.force_cpu_only, quantized,
            )
        except Exception as e:
            self.logger.error(f"Failed to load MedMO model: {e}")
            self.model = None
            self.processor = None

    def set_generation_model(self, model_id: str) -> str:
        self.generation_model_id = model_id
        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size: int) -> str:
        raise NotImplementedError(
            "MedMOProvider does not support a separate embedding model. "
            "Embeddings are generated from the local model path directly."
        )

    def generate_text(self, prompt: str, chat_history: list = None,
                      max_output_tokens: int = None, temp: float = None,
                      image_path: str = None) -> str:
        if not self.model or not self.processor:
            self.logger.error("MedMO model is not loaded.")
            return None

        if chat_history is None:
            chat_history = []

        # Normalize chat history to Qwen format (role + content list)
        normalized_history = []
        for msg in chat_history:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "user")).lower()
            if role == "system":
                normalized_history.append({
                    "role": "system",
                    "content": [{"type": "text", "text": str(msg.get("message") or msg.get("content") or "")}],
                })
            elif role in ("assistant", "chatbot"):
                text = str(msg.get("message") or msg.get("content") or "")
                if isinstance(msg.get("content"), list):
                    normalized_history.append({"role": "assistant", "content": msg["content"]})
                else:
                    normalized_history.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": text}],
                    })
            else:
                text = str(msg.get("message") or msg.get("content") or "")
                if isinstance(msg.get("content"), list):
                    normalized_history.append({"role": "user", "content": msg["content"]})
                else:
                    normalized_history.append({
                        "role": "user",
                        "content": [{"type": "text", "text": text}],
                    })

        current_turn = self._build_user_turn(prompt=prompt, image_path=image_path)
        messages = normalized_history + [current_turn]

        try:
            from qwen_vl_utils import process_vision_info
            import time as _time

            gen_started = _time.perf_counter()
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

            actual_temp = temp if temp is not None else self.default_temp
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_output_tokens or self.default_output_max_tokens,
                temperature=actual_temp,
                do_sample=actual_temp > 0,
                repetition_penalty=1.15,
            )

            trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self.processor.batch_decode(
                trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )

            self.logger.info("MedMO generation took %.2fs", _time.perf_counter() - gen_started)

            if not output_text:
                self.logger.error("MedMO returned empty output.")
                return None

            return output_text[0]

        except Exception as e:
            self.logger.error(f"MedMO generation error: {e}")
            return None

    def embed_text(self, text: str, document_type: str = None) -> list:
        """MedMO is a generative vision-language model — embeddings not supported."""
        raise NotImplementedError(
            "MedMOProvider does not support text embedding. "
            "Use an embedding-specific provider instead."
        )

    def construct_prompt(self, query: str, role: str) -> dict:

        return {
            "role": role,
            "content": [
                {"type": "text", "text": self.process_text(query)}
            ],
        }


    def process_text(self, text: str) -> str:
        """Truncate and strip the input text."""
        return text[: self.default_input_max_characters].strip()

    def _build_user_turn(self, prompt: str, image_path: str = None) -> dict:

        content = []

        if image_path:
            content.append({"type": "image", "image": image_path})

        content.append({"type": "text", "text": self.process_text(prompt)})

        return {
            "role": MedMOEnums.user.value,
            "content": content,
        }