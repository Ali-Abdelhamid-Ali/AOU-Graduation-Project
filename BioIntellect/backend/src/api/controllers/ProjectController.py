from .BaseController import BaseController
import os 
import uuid


class projectController(BaseController) :
        def __init__(self):
            super().__init__() 

        def get_project_path(self,project_id:str):
            cleaned_project_id = (project_id or "").strip()
            try:
                uuid.UUID(cleaned_project_id)
            except Exception as exc:
                raise ValueError("project_id must be a valid UUID") from exc

            base_dir = os.path.realpath(self.file_dir)
            project_dir = os.path.realpath(os.path.join(base_dir, cleaned_project_id))

            if not project_dir.startswith(base_dir + os.sep):
                raise ValueError("project_id resolves outside the allowed directory")


            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            

            return project_dir