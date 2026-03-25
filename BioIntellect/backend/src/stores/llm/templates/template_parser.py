import os
from string import Template

class template_parser:
    def __init__(self,language:str, default_language="en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))

        self.language = default_language
        self.default_language = default_language
        self.set_language(language)
    def set_language(self, language:str):
        if not language:
            language = self.default_language
        if language and os.path.exists(os.path.join(self.current_path, "locales", language, "rag.py")):
            self.language = language
        else:
            self.language = self.default_language
    def get(self, group:str , key:str, vars:dict ) -> str :
        if not group or not key:
            return ""
        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py")
        tsrgeted_language = self.language
        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales", self.default_language, f"{group}.py")
            tsrgeted_language = self.default_language

            if not os.path.exists(group_path):
                return ""

        module=__import__(f"src.stores.llm.templates.locales.{tsrgeted_language}.{group}", fromlist=[key])

        
        template_str = getattr(module, key, "")
        if not template_str:
            return ""
        template = Template(template_str)
        return template.substitute(**vars)