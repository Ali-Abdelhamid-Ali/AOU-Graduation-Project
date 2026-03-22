from .providers.CoHereProvider import CoHereProvider
from .providers.MedMOProvider   import MedMOProvider
from .providers.OpenAIProvider import OpenAIProvider
from .providers.PhiQAProvider   import PhiQAProvider


class LLMProviderFactory:
    def __init__(self, settings):
        self.settings = settings

    def create(self, backend: str):
        backend = (backend or "").strip().lower()
        try:
            if backend == "cohere":
                return CoHereProvider(api_key=self.settings.COHERE_API_KEY,
                                    default_input_max_characters=self.settings.INPUT_DEFAULT_MAX_CHARACTERS,
                                    default_output_max_tokens=self.settings.INPUT_DEFAULT_MAX_TOKENS,
                                    default_temp=self.settings.INPUT_DEFAULT_TEMPERATURE
                                    )
            elif backend == "openai":
                return OpenAIProvider(api_key=self.settings.OPENAI_API_KEY,
                                    api_url=self.settings.OPENAI_API_URL,
                                    default_input_max_characters=self.settings.INPUT_DEFAULT_MAX_CHARACTERS,
                                    default_output_max_tokens=self.settings.INPUT_DEFAULT_MAX_TOKENS,
                                    default_temp=self.settings.INPUT_DEFAULT_TEMPERATURE
                                    )
            elif backend == "medmo":
                return MedMOProvider(
                    model_path=self.settings.MEDMO_MODEL_PATH,
                    default_input_max_characters=self.settings.INPUT_DEFAULT_MAX_CHARACTERS,
                    default_output_max_tokens=self.settings.INPUT_DEFAULT_MAX_TOKENS,
                    default_temp=self.settings.INPUT_DEFAULT_TEMPERATURE,
                    offload_folder=self.settings.MEDMO_OFFLOAD_FOLDER,
                                        )
            elif backend == "phi_qa":
                return PhiQAProvider(
                    model_path=self.settings.PHI_QA_MODEL_PATH,
                    default_input_max_characters=self.settings.INPUT_DEFAULT_MAX_CHARACTERS,
                    default_output_max_tokens=self.settings.INPUT_DEFAULT_MAX_TOKENS,
                    default_temp=self.settings.INPUT_DEFAULT_TEMPERATURE,
                                        )
            else:
                raise ValueError(f"Unsupported backend: {backend}")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize backend '{backend}': {exc}"
            ) from exc