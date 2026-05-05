import gc
import os
import sys
import threading
import time
from typing import Any, Optional

import torch

# CRITICAL: Import unsloth BEFORE transformers to apply optimizations
_UNSLOTH_AVAILABLE = False
FastLanguageModel = None


def _try_import_unsloth() -> bool:
    """Attempt to import unsloth only if CUDA is available."""
    global FastLanguageModel, _UNSLOTH_AVAILABLE
    logger = get_logger("provider.PhiQAProvider")
    
    if not torch.cuda.is_available():
        logger.warning("[PhiQA] CUDA not available — skipping unsloth import")
        return False
    
    try:
        logger.info("[PhiQA] CUDA detected — attempting unsloth import …")
        from unsloth import FastLanguageModel as _FL
        FastLanguageModel = _FL
        _UNSLOTH_AVAILABLE = True
        logger.info("[PhiQA] Unsloth imported successfully")
        return True
    except Exception as e:
        logger.error("[PhiQA] Unsloth import failed: %s", e, exc_info=True)
        return False


from transformers import AutoModelForCausalLM, AutoTokenizer

from ..LLMInterface import LLMInterface
from ..LLMEnums import PhiQAEnums
from src.observability.logger import get_logger


_SYSTEM_PROMPT = (
    "You must answer only using information explicitly provided in the user message.\n"
    "Do not add external knowledge.\n"
    "Do not assume missing facts.\n"
    "If the information is not present reply: "
    '"The context does not contain this information."\n'
    "Maintain a neutral, clear, and factual tone (C2 English level)."
)


class PhiQAProvider(LLMInterface):
    def __init__(
        self,
        model_path: str,
        default_input_max_characters: int = 6000,
        default_output_max_tokens: int = 1024,
        default_max_input_tokens: int = 4048,
        force_cpu_only: bool = False,
    ):
        self.logger = get_logger("provider.PhiQAProvider")

        cuda_available = torch.cuda.is_available()
        unsloth_available = _try_import_unsloth()
        self.logger.info(
            "[PhiQA] CUDA available: %s | Unsloth available: %s | Python: %s",
            cuda_available, unsloth_available, sys.executable,
        )

        self.model_path = model_path
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_max_input_tokens = default_max_input_tokens
        self.force_cpu_only = force_cpu_only
        self.Enums = PhiQAEnums
        self.generation_model_id = model_path
        self.embedding_model_id = model_path
        self.embedding_size: Optional[int] = None
        self.model: Any = None
        self.tokenizer: Any = None
        self.is_cpu_mode: bool = False

        self._generate_lock = threading.Lock()

        self.logger.info("Loading PhiQA model from: %s", self.model_path)

        load_started = time.perf_counter()
        skip_4bit = os.getenv("PHIQA_SKIP_4BIT", "false").lower() in ("1", "true", "yes")
        use_cpu_loader = self.force_cpu_only or not _UNSLOTH_AVAILABLE
        loader_name = "transformers-cpu" if use_cpu_loader else "unsloth"

        try:
            if use_cpu_loader:
                self.model, self.tokenizer = self._load_with_transformers_cpu()
                self.is_cpu_mode = True
            else:
                self.model, self.tokenizer = self._load_with_unsloth(skip_4bit=skip_4bit)
                self.is_cpu_mode = False
            self.model.eval()
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "right"

            template_path = os.path.join(self.model_path, "chat_template.jinja")
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    self.tokenizer.chat_template = f.read()
                self.logger.info("Loaded custom chat template from %s", template_path)
            else:
                self.logger.warning("chat_template.jinja not found at %s", template_path)

            try:
                self.embedding_size = int(self.model.config.hidden_size)
            except AttributeError:
                self.embedding_size = None

            actual_device = str(self.model.device)
            if not self.is_cpu_mode and "cuda" not in actual_device:
                self.logger.error(
                    "[PhiQA] DEVICE MISMATCH — expected GPU but model is on %s", actual_device
                )
                raise RuntimeError(
                    f"PhiQA loaded via unsloth but model.device={actual_device}. "
                    "Check CUDA installation and conda environment."
                )

            self.logger.info(
                "[PhiQA] Model loaded — device=%s | loader=%s | load_s=%.2f | embedding_size=%s",
                actual_device, loader_name,
                time.perf_counter() - load_started,
                self.embedding_size,
            )
        except Exception as load_exc:
            self.model = None
            self.tokenizer = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise RuntimeError(
                f"Failed to load PhiQA via {loader_name}. Last error: {load_exc}"
            ) from load_exc

    def _load_with_unsloth(self, skip_4bit: bool) -> tuple[Any, Any]:
        if FastLanguageModel is None:
            raise RuntimeError("Unsloth is not available in this runtime.")
        self.logger.info("Attempting PhiQA load with strategy: unsloth")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_path,
            max_seq_length=self.default_max_input_tokens,
            load_in_4bit=(not skip_4bit),
            low_cpu_mem_usage=True,
        )
        model = FastLanguageModel.for_inference(model)
        return model, tokenizer

    def _load_with_transformers_cpu(self) -> tuple[Any, Any]:
        # Unsloth requires an accelerator; CPU-only runtimes load the merged checkpoint
        # directly through Transformers instead.
        strategies: list[tuple[str, torch.dtype]] = [
            ("bfloat16", torch.bfloat16),
            ("float32", torch.float32),
        ]
        last_exc: Optional[Exception] = None

        for strategy_name, dtype in strategies:
            try:
                self.logger.info(
                    "Attempting PhiQA load with strategy: transformers-cpu-%s",
                    strategy_name,
                )
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    low_cpu_mem_usage=True,
                    dtype=dtype,
                    device_map="auto",
                    trust_remote_code=True,
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                )
                return model, tokenizer
            except Exception as exc:
                last_exc = exc
                self.logger.warning(
                    "PhiQA CPU load strategy %s failed: %s",
                    strategy_name,
                    exc,
                )
                gc.collect()

        raise RuntimeError(
            f"All CPU loading strategies failed. Last error: {last_exc}"
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

    def generate_text(
        self,
        prompt: str,
        chat_history: Optional[list] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Optional[str]:
        self.logger.info("=" * 60)
        self.logger.info(
            "[PhiQA] generate_text CALLED | prompt_len=%d | history_msgs=%d",
            len(prompt), len(chat_history or []),
        )

        if not self.model or not self.tokenizer:
            raise RuntimeError("PhiQA model is not loaded.")

        # --- STEP 1: normalise history ---
        normalized: list[dict] = [{"role": PhiQAEnums.system.value, "content": _SYSTEM_PROMPT}]
        for msg in (chat_history or []):
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "user")).lower()
            raw_content = msg.get("content")
            if isinstance(raw_content, list):
                text = " ".join(
                    str(b.get("text", ""))
                    for b in raw_content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            else:
                text = str(raw_content or msg.get("message") or "")
            if not text.strip():
                continue
            if role in ("assistant", "chatbot"):
                role = "assistant"
            elif role == "system":
                continue
            else:
                role = "user"
            normalized.append({"role": role, "content": text})

        normalized.append({"role": PhiQAEnums.user.value, "content": f"Input:\n{prompt}"})
        self.logger.info("[PhiQA] STEP 1 DONE — context messages: %d", len(normalized))

        # --- STEP 2: chat template ---
        if hasattr(self.tokenizer, "apply_chat_template") and getattr(self.tokenizer, "chat_template", None):
            input_text = self.tokenizer.apply_chat_template(
                normalized, tokenize=False, add_generation_prompt=True
            )
        else:
            input_text = self._build_plain_prompt(normalized)
        self.logger.info("[PhiQA] STEP 2 DONE — input_text_len=%d chars", len(input_text))

        # --- STEP 3: tokenize ---
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=self.default_max_input_tokens,
        ).to(self.model.device)
        input_token_count = inputs.input_ids.shape[-1]
        self.logger.info(
            "[PhiQA] STEP 3 DONE — input_tokens=%d | device=%s",
            input_token_count, self.model.device,
        )

        # --- STEP 4: generate (P0-FIX: thread lock, P1-FIX: no SIGALRM) ---
        token_cap = 100 if self.is_cpu_mode else 512
        max_new = min(max_output_tokens or self.default_output_max_tokens, token_cap)
        if self.is_cpu_mode:
            self.logger.warning("[PhiQA] CPU mode — capped max_new_tokens to %d", max_new)

        gen_kwargs = {
            "max_new_tokens": max_new,
            "do_sample": False,
            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "use_cache": True,
        }

        self.logger.info("[PhiQA] STEP 4 — acquiring generate lock …")
        with self._generate_lock:
            self.logger.info("[PhiQA] STEP 4 — model.generate starting | max_new=%d", max_new)
            t0 = time.perf_counter()
            try:
                with torch.inference_mode():
                    generated_ids = self.model.generate(**inputs, **gen_kwargs)
            finally:
                generate_s = time.perf_counter() - t0
                output_token_count = generated_ids.shape[-1] - input_token_count if 'generated_ids' in dir() else 0
                self.logger.info(
                    "[PhiQA] STEP 4 DONE — generate_s=%.2f | output_tokens=%d | tok/s=%.2f",
                    generate_s, output_token_count,
                    output_token_count / generate_s if generate_s > 0 else 0,
                )

        # --- STEP 5: decode ---
        new_tokens = generated_ids[0][input_token_count:]
        output_text = self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        ).strip()

        # P1-FIX: release GPU memory immediately after decode
        del generated_ids, new_tokens, inputs
        if not self.is_cpu_mode:
            torch.cuda.empty_cache()

        if not output_text:
            raise RuntimeError("PhiQA returned empty output.")

        self.logger.info(
            "[PhiQA] COMPLETE — output_len=%d chars | total_s=%.2f",
            len(output_text), time.perf_counter() - t0,
        )
        self.logger.info("=" * 60)
        return output_text

    def embed_text(
        self, text: "str | list[str]", document_type: Optional[str] = None
    ) -> "Optional[list]":
        """Embed one string or a list of strings.

        Returns a single vector (list[float]) when *text* is a str, or a list
        of vectors (list[list[float]]) when *text* is a list — matching the
        contract used by CoHereProvider so callers can treat both providers
        identically.
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("PhiQA model is not loaded.")

        is_batch = isinstance(text, list)
        texts: list[str] = text if is_batch else [text]
        results: list[list[float]] = []

        for item in texts:
            inputs = self.tokenizer(
                self.process_text(item),
                return_tensors="pt",
                truncation=True,
                max_length=self.default_max_input_tokens,
            ).to(self.model.device)

            with torch.inference_mode():
                outputs = self.model(**inputs, output_hidden_states=True)

            if outputs.hidden_states is None:
                raise RuntimeError("Model did not return hidden_states.")

            last_hidden = outputs.hidden_states[-1]
            mask = inputs["attention_mask"].to(last_hidden.dtype).unsqueeze(-1)
            pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=-1).squeeze(0)
            embedding = pooled.detach().cpu().float().tolist()

            del inputs, outputs, last_hidden, pooled
            if not self.is_cpu_mode:
                torch.cuda.empty_cache()

            if self.embedding_size is None:
                self.embedding_size = len(embedding)
            results.append(embedding)

        return results if is_batch else results[0]

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
