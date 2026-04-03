from .BaseController import BaseController
from src.api.controllers.ProjectController import projectController
import re
from fastapi import  UploadFile 
from fastapi import HTTPException
import os 

class DataController(BaseController) :
        def __init__(self):
            super().__init__() #دي علشان يروح يفعل الكلاس الاب علشان اعرف اخد منه الاعداتا و اي حاجه جواها بعدين 
            self.size_scale=1048576
        def validate_uploaded_file(self,file: UploadFile):
              
            if file.content_type not in self.app_settings.FILE_ALLOWED_TYPE:
                    raise HTTPException(
                    status_code=400,
                    detail=f"File type '{file.content_type}' not allowed"
                    )
            return True
        

        def generate_unique_filepath(self, orig_file_name: str, project_id: str):
            random_key = self.generate_random_string()
            project_path = projectController().get_project_path(project_id=project_id)
            cleand_file_name = self.get_clean_file_name(orig_file_name=orig_file_name)
            
            new_file_path = os.path.join(project_path, random_key + "_" + cleand_file_name)
            
            while os.path.exists(new_file_path):
                random_key = self.generate_random_string()
                new_file_path = os.path.join(project_path, random_key + "_" + cleand_file_name)
            
            return new_file_path , random_key + "_" + cleand_file_name
        

        def get_clean_file_name(self, orig_file_name: str) -> str:
            cleaned_file_name = re.sub(r'[^\w.]', '_', orig_file_name.strip())
            cleaned_file_name=cleaned_file_name.replace(" ", "_")
            return cleaned_file_name

              