import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLForConditionalGeneration
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info

from ..LLMInterface import LLMInterface
from ..LLMEnums import MedMOEnums
from src.observability.logger import get_logger


class MedMOProvider(LLMInterface):


    def __init__(self,model_path: str,default_input_max_characters: int = 1000,
    default_output_max_tokens: int = 512,default_temp: float = 0.1,
    offload_folder: str = "./offload",):
        self.model_path = model_path
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.offload_folder = offload_folder

        # These are kept to satisfy the interface but are unused for local models
        self.generation_model_id = model_path
        self.embedding_model_id = None
        self.embedding_size = None

        self.logger = get_logger("provider.MedMOProvider")

        self.logger.info(f"Loading MedMO model from: {self.model_path}")
        try:
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
                offload_folder=self.offload_folder,
            )
            self.processor = AutoProcessor.from_pretrained(self.model_path)
            self.logger.info("MedMO model loaded successfully.")
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

    def generate_text(self,prompt: str,chat_history: list = None,max_output_tokens: int = None,
        temp: float = None,image_path: str = None) -> str:
        if not self.model or not self.processor:
            self.logger.error("MedMO model is not loaded.")
            return None

        if chat_history is None:
            chat_history = []

        current_turn = self._build_user_turn(prompt=prompt, image_path=image_path)

        messages = chat_history + [current_turn]

        try:
            text_input = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)

            inputs = self.processor(text=[text_input],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to(self.model.device)

            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_output_tokens or self.default_output_max_tokens,
                temperature=temp if temp is not None else self.default_temp,
                do_sample=(temp if temp is not None else self.default_temp) > 0,
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