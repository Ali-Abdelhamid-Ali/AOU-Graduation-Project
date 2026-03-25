import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..LLMInterface import LLMInterface
from ..LLMEnums import PhiQAEnums
from src.observability.logger import get_logger


class PhiQAProvider(LLMInterface):
    def __init__(self,model_path: str,default_input_max_characters: int = 1000,default_output_max_tokens: int = 512,default_temp: float = 0.1):
        self.model_path = model_path
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.Enums = PhiQAEnums
        self.generation_model_id = model_path
        self.embedding_model_id = None
        self.embedding_size = None

        self.logger = get_logger("provider.PhiQAProvider")

        self.logger.info(f"Loading PhiQA model from: {self.model_path}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path,trust_remote_code=True,)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
            self.model.eval()
            self.logger.info("PhiQA model loaded successfully.")
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

    def generate_text(self,prompt: str,chat_history: list = None,max_output_tokens: int = None,temp: float = None) -> str:

        if not self.model or not self.tokenizer:
            self.logger.error("PhiQA model is not loaded.")
            return None

        if chat_history is None:
            chat_history = []

        messages = list(chat_history)
        messages.append(self.construct_prompt(query=prompt, role=PhiQAEnums.user.value))

        try:
            if hasattr(self.tokenizer, "apply_chat_template"):
                input_text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                input_text = self._build_plain_prompt(messages)

            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                truncation=True,
                max_length=self.default_input_max_characters,
            ).to(self.model.device)

            actual_temp = temp if temp is not None else self.default_temp

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens or self.default_output_max_tokens,
                    temperature=actual_temp,
                    do_sample=actual_temp > 0,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            new_tokens = generated_ids[0][inputs.input_ids.shape[-1]:]
            output_text = self.tokenizer.decode(
                new_tokens,skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            ).strip()

            if not output_text:
                self.logger.error("PhiQA returned empty output.")
                return None

            return output_text

        except Exception as e:
            self.logger.error(f"PhiQA generation error: {e}")
            return None

    def embed_text(self, text: str, document_type: str = None) -> list:

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

    def _build_plain_prompt(self, messages: list) -> str:
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