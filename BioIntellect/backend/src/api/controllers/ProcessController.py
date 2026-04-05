from .BaseController import BaseController

import os
from .ProjectController import projectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class _DocxLoader:
    """Minimal loader for .docx files using python-docx."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list:
        try:
            import docx  # python-docx
        except ImportError as exc:
            raise ImportError(
                "python-docx is required to load .docx files. "
                "Install it with: pip install python-docx"
            ) from exc

        doc = docx.Document(self.file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
        return [Document(page_content=text, metadata={"source": self.file_path})]


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
        elif file_ext==".docx":
            return _DocxLoader(file_path)
        else:
            raise ValueError(f"unsupported file type: {file_ext}")
        


    def get_file_content(self,file_id:str):
        loader=self.get_file_loader(file_id=file_id)
        return loader.load()
    
    def process_file_content(self,file_content:list , file_id:str,chunk_size:int=1000,overlap_size:int=200):
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                     chunk_overlap=overlap_size,
                                                     length_function=len)
        

        file_content_text=[doc.page_content for doc in file_content]
        file_content_metadata=[doc.metadata for doc in file_content]

        chunk=text_splitter.create_documents(
            file_content_text,
            metadatas=file_content_metadata)

        return chunk