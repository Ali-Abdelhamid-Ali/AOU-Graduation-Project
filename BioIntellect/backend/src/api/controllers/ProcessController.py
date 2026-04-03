from .BaseController import BaseController

import os 
from .ProjectController import projectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ProcessController(BaseController) :

    def __init__(self,project_id:str):
        super().__init__()
        self.project_id=project_id
        self.project_path=projectController().get_project_path(project_id=project_id)
    def get_file_extension(self,file_id:str):
        return os.path.splitext(file_id)[1].lower()
    def get_file_loader(self,file_id:str):
        file_ext=self.get_file_extension(file_id=file_id)
        base_dir = os.path.realpath(self.project_path)
        file_path=os.path.realpath(os.path.join(base_dir,file_id))

        if not file_path.startswith(base_dir + os.sep):
            raise ValueError("file_id resolves outside the allowed directory")

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if file_ext in [".txt",".md"]:
            return TextLoader(file_path,encoding="utf-8",autodetect_encoding=True)
        elif file_ext==".pdf":
            return PyPDFLoader(file_path)
        else:
            raise ValueError(f"unsupported file type: {file_ext}")
        


    def get_file_content(self,file_id:str):
        loader=self.get_file_loader(file_id=file_id)
        return loader.load()
    
    def process_file_content(self,file_content:list , file_id:str,chunk_size:int=100,overlap_size:int=20):
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                     chunk_overlap=overlap_size,
                                                     length_function=len)
        

        file_content_text=[doc.page_content for doc in file_content]
        file_content_metadata=[doc.metadata for doc in file_content]

        chunk=text_splitter.create_documents(
            file_content_text,
            metadatas=file_content_metadata)

        return chunk