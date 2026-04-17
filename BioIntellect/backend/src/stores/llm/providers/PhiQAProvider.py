import gc
import os
import time
from typing import Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..LLMInterface import LLMInterface
from ..LLMEnums import PhiQAEnums
from src.observability.logger import get_logger


class PhiQAProvider(LLMInterface):
    def __init__(self, model_path: str, default_input_max_characters: int = 6000,
                 default_output_max_tokens: int = 1024, default_temp: float = 0.3,
                 default_max_input_tokens: int = 2048, force_cpu_only: bool = False):
        self.model_path = model_path
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_max_input_tokens = default_max_input_tokens
        self.default_temp = default_temp
        self.force_cpu_only = force_cpu_only
        self.Enums = PhiQAEnums
        self.generation_model_id = model_path
        self.embedding_model_id = model_path
        self.embedding_size: Optional[int] = None
        self.model: Any = None
        self.tokenizer: Any = None

        self.logger = get_logger("provider.PhiQAProvider")
        self.logger.info("Loading PhiQA model from: %s", self.model_path)

        load_started = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        has_accelerate = False
        try:
            import accelerate  # noqa: F401
            has_accelerate = True
        except ImportError:
            self.logger.warning("accelerate not installed — device_map disabled")

        skip_4bit = os.getenv("PHIQA_SKIP_4BIT", "false").lower() in ("1", "true", "yes")

        load_strategies: list[tuple[str, dict]] = []
        if not self.force_cpu_only and not skip_4bit:
            try:
                from transformers import BitsAndBytesConfig
                import bitsandbytes  # noqa: F401
                q_kwargs: dict = {
                    "low_cpu_mem_usage": True,
                    "trust_remote_code": True,
                    "quantization_config": BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    ),
                }
                if has_accelerate:
                    q_kwargs["device_map"] = "auto"
                load_strategies.append(("4bit", q_kwargs))
            except ImportError:
                pass

            fp16_kwargs: dict = {
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
                "trust_remote_code": True,
            }
            if has_accelerate:
                fp16_kwargs["device_map"] = "auto"
            load_strategies.append(("float16", fp16_kwargs))

        load_strategies.append(("float32-cpu", {
            "torch_dtype": torch.float32,
            "low_cpu_mem_usage": True,
            "trust_remote_code": True,
        }))

        last_exc: Optional[Exception] = None
        for strategy_name, kwargs in load_strategies:
            try:
                self.logger.info("Attempting PhiQA load with strategy: %s", strategy_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_path, **kwargs)
                self.model.eval()
                try:
                    self.embedding_size = int(self.model.config.hidden_size)
                except AttributeError:
                    self.embedding_size = None
                try:
                    device_map = getattr(self.model, "hf_device_map", None) or {"model": str(self.model.device)}
                except Exception:
                    device_map = "unknown"
                self.logger.info(
                    "PhiQA model loaded (%s, load_s=%.2f, embedding_size=%s, devices=%s).",
                    strategy_name, time.perf_counter() - load_started, self.embedding_size, device_map,
                )
                return
            except Exception as load_exc:
                self.logger.warning("Strategy %s failed: %s", strategy_name, load_exc)
                last_exc = load_exc
                self.model = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        raise RuntimeError(
            f"All loading strategies failed for PhiQA. Last error: {last_exc}"
        ) from last_exc

    def set_generation_model(self, model_id: str) -> str:
        self.generation_model_id = model_id
        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size: int) -> str:
        # PhiQA reuses the causal LM hidden state for embeddings — no separate
        # model is loaded. We accept the id/size to keep the interface consistent.
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        return self.embedding_model_id

    def generate_text(self, prompt: str, chat_history: Optional[list] = None,
                      max_output_tokens: Optional[int] = None,
                      temp: Optional[float] = None) -> Optional[str]:
        if not self.model or not self.tokenizer:
            raise RuntimeError("PhiQA model is not loaded.")

        normalized: list[dict] = []
        for msg in (chat_history or []):
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "user")).lower()
            raw_content = msg.get("content")
            if isinstance(raw_content, list):
                # Flatten Qwen-style content blocks into plain text for Phi.
                text = " ".join(
                    str(block.get("text", ""))
                    for block in raw_content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = str(raw_content or msg.get("message") or "")
            if not text.strip():
                continue
            if role in ("assistant", "chatbot"):
                role = "assistant"
            elif role == "system":
                role = "system"
            else:
                role = "user"
            normalized.append({"role": role, "content": text})

        normalized.append({"role": PhiQAEnums.user.value, "content": prompt})

        try:
            generation_started = time.perf_counter()
            if hasattr(self.tokenizer, "apply_chat_template") and getattr(self.tokenizer, "chat_template", None):
                input_text = self.tokenizer.apply_chat_template(
                    normalized,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                input_text = self._build_plain_prompt(normalized)

            tokenize_started = time.perf_counter()
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                truncation=True,
                max_length=self.default_max_input_tokens,
            ).to(self.model.device)
            tokenize_s = time.perf_counter() - tokenize_started

            actual_temp = self.default_temp if temp is None else temp
            do_sample = actual_temp is not None and actual_temp > 0

            gen_kwargs: dict = {
                "max_new_tokens": max_output_tokens or self.default_output_max_tokens,
                "do_sample": do_sample,
                "repetition_penalty": 1.15,
                "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "use_cache": True,
            }
            if do_sample:
                gen_kwargs["temperature"] = float(actual_temp)

            model_started = time.perf_counter()
            with torch.inference_mode():
                generated_ids = self.model.generate(**inputs, **gen_kwargs)
            model_s = time.perf_counter() - model_started

            new_tokens = generated_ids[0][inputs.input_ids.shape[-1]:]
            output_text = self.tokenizer.decode(
                new_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            ).strip()

            if not output_text:
                raise RuntimeError("PhiQA returned empty output.")

            self.logger.info(
                "PhiQA generation timings tokenize_s=%.2f generate_s=%.2f total_s=%.2f",
                tokenize_s, model_s, time.perf_counter() - generation_started,
            )
            return output_text

        except RuntimeError:
            raise
        except Exception as e:
            self.logger.error("PhiQA generation error: %s", e)
            raise

    def embed_text(self, text: str, document_type: Optional[str] = None) -> Optional[list[float]]:
        if not self.model or not self.tokenizer:
            raise RuntimeError("PhiQA model is not loaded.")

        try:
            # Use the model's true context limit (tokens) — not characters.
            inputs = self.tokenizer(
                self.process_text(text),
                return_tensors="pt",
                truncation=True,
                max_length=self.default_max_input_tokens,
            ).to(self.model.device)

            with torch.inference_mode():
                outputs = self.model(**inputs, output_hidden_states=True)

            last_hidden_state = outputs.hidden_states[-1]
            # Cast attention_mask to hidden-state dtype so the product is numerically clean.
            attention_mask = inputs["attention_mask"].to(last_hidden_state.dtype).unsqueeze(-1)
            summed = (last_hidden_state * attention_mask).sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1e-9)
            pooled = summed / counts

            # L2-normalize so cosine similarity == dot product downstream.
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=-1).squeeze(0)

            embedding = pooled.detach().cpu().float().tolist()
            if self.embedding_size is None:
                self.embedding_size = len(embedding)
            return embedding

        except Exception as e:
            self.logger.error("PhiQA embedding error: %s", e)
            raise

    def construct_prompt(self, query: str, role: str) -> dict:
        return {
            "role": role,
            "content": query,
        }

    def process_text(self, text: str) -> str:
        return text[: self.default_input_max_characters].strip()

    def _build_plain_prompt(self, messages: list[Any]) -> str:
        role_map = {
            PhiQAEnums.system.value: "System",
            PhiQAEnums.user.value: "Human",
            PhiQAEnums.assistant.value: "Assistant",
        }
        parts = [
            f"{role_map.get(msg.get('role', ''), 'Human')}: {msg.get('content', '')}"
            for msg in messages
        ]
        parts.append("Assistant:")
        return "\n".join(parts)
