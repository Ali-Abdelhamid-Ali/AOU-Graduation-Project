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
        self.embedding_model_id = None
        self.embedding_size = None
        self.model: Any = None
        self.tokenizer: Any = None

        self.logger = get_logger("provider.PhiQAProvider")

        self.logger.info(f"Loading PhiQA model from: {self.model_path}")
        load_started = time.perf_counter()
        try:
            load_kwargs: dict = {
                "low_cpu_mem_usage": True,
                "trust_remote_code": True,
            }

            # Use 4-bit quantization when available for faster inference
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
                    self.logger.info("Using 4-bit quantization for PhiQA.")
                except ImportError:
                    self.logger.info("bitsandbytes not available — falling back to float16.")
                    load_kwargs["torch_dtype"] = torch.float16

                try:
                    import accelerate  # noqa: F401
                    load_kwargs["device_map"] = "auto"
                except ImportError:
                    self.logger.warning("accelerate not installed — loading PhiQA on CPU")
            else:
                load_kwargs["torch_dtype"] = torch.float32

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path, **load_kwargs)

            self.model.eval()
            self.logger.info(
                "PhiQA model loaded (force_cpu=%s, quantized=%s, load_s=%.2f).",
                self.force_cpu_only, quantized,
                time.perf_counter() - load_started,
            )
        except Exception as e:
            self.logger.error(f"Failed to load PhiQA model: {e}")
            self.model = None
            self.tokenizer = None



    def set_generation_model(self, model_id: str) -> str:

        self.generation_model_id = model_id
        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size: int) -> str:
        raise NotImplementedError(
            "PhiQAProvider does not support a separate embedding model. "
            "Embeddings are generated from the local model path directly."
        )

    def generate_text(self, prompt: str, chat_history: Optional[list] = None,
                      max_output_tokens: Optional[int] = None,
                      temp: Optional[float] = None) -> Optional[str]:
        if not self.model or not self.tokenizer:
            self.logger.error("PhiQA model is not loaded.")
            return None

        if chat_history is None:
            chat_history = []

        # Normalize chat history to standard {role, content} format
        normalized: list[dict] = []
        for msg in chat_history:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "user")).lower()
            text = str(msg.get("content") or msg.get("message") or "")
            if not text.strip():
                continue
            if role in ("assistant", "chatbot"):
                role = "assistant"
            elif role == "system":
                role = "system"
            else:
                role = "user"
            normalized.append({"role": role, "content": text})

        normalized.append(self.construct_prompt(query=prompt, role=PhiQAEnums.user.value))

        try:
            generation_started = time.perf_counter()
            if hasattr(self.tokenizer, "apply_chat_template"):
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

            actual_temp = temp if temp is not None else self.default_temp

            model_started = time.perf_counter()
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens or self.default_output_max_tokens,
                    temperature=actual_temp,
                    do_sample=actual_temp > 0,
                    repetition_penalty=1.15,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            model_s = time.perf_counter() - model_started

            new_tokens = generated_ids[0][inputs.input_ids.shape[-1]:]
            output_text = self.tokenizer.decode(
                new_tokens, skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            ).strip()

            if not output_text:
                self.logger.error("PhiQA returned empty output.")
                return None

            self.logger.info(
                "PhiQA generation timings tokenize_s=%.2f generate_s=%.2f total_s=%.2f",
                tokenize_s, model_s, time.perf_counter() - generation_started,
            )
            return output_text

        except Exception as e:
            self.logger.error(f"PhiQA generation error: {e}")
            return None

    def embed_text(self, text: str, document_type: Optional[str] = None) -> Optional[list[float]]:

        if not self.model or not self.tokenizer:
            self.logger.error("PhiQA model is not loaded.")
            return None

        try:
            inputs = self.tokenizer(
                self.process_text(text),
                return_tensors="pt",
                truncation=True,
                max_length=self.default_input_max_characters,
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model(
                    **inputs,
                    output_hidden_states=True,
                )

            # Mean-pool the last hidden state over the sequence dimension
            last_hidden_state = outputs.hidden_states[-1]         
            attention_mask = inputs["attention_mask"].unsqueeze(-1) 
            summed = (last_hidden_state * attention_mask).sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1e-9)
            embedding = (summed / counts).squeeze(0)               

            return embedding.cpu().float().tolist()

        except Exception as e:
            self.logger.error(f"PhiQA embedding error: {e}")
            return None

    def construct_prompt(self, query: str, role: str) -> dict:
        return {
            "role": role,
            "content": self.process_text(query),
        }



    def process_text(self, text: str) -> str:
        return text[: self.default_input_max_characters].strip()

    def _build_plain_prompt(self, messages: list[Any]) -> str:
        parts = []
        role_map = {
            PhiQAEnums.system.value: "System",
            PhiQAEnums.user.value: "Human",
            PhiQAEnums.assistant.value: "Assistant",
        }
        for msg in messages:
            role_label = role_map.get(msg.get("role", ""), "Human")
            parts.append(f"{role_label}: {msg.get('content', '')}")
        parts.append("Assistant:")
        return "\n".join(parts)