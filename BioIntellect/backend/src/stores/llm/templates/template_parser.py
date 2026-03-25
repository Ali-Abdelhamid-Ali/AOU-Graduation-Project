import os
from functools import lru_cache
from string import Template
from typing import Any


class template_parser:
    def __init__(self, language: str, default_language: str = "en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))

        self.language = default_language
        self.default_language = default_language
        self.set_language(language)

    def set_language(self, language: str):
        if not language:
            language = self.default_language
        if language and os.path.exists(os.path.join(self.current_path, "locales", language, "rag.py")):
            self.language = language
        else:
            self.language = self.default_language

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_template(language: str, default_language: str, group: str, key: str) -> str:
        for target_language in (language, default_language):
            try:
                module = __import__(f"src.stores.llm.templates.locales.{target_language}.{group}", fromlist=[key])
            except ModuleNotFoundError:
                continue

            template_str = getattr(module, key, "")
            if template_str:
                return template_str

        return ""

    def get(self, group: str, key: str, vars: dict[str, Any] | None = None) -> str:
        if not group or not key:
            return ""
        template_str = self._get_template(
            language=self.language,
            default_language=self.default_language,
            group=group,
            key=key,
        )
        if not template_str:
            return ""
        template = Template(template_str)
        return template.substitute(**(vars or {}))