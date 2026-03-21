from fastapi import APIRouter, Depends, UploadFile 
from fastapi.responses import JSONResponse
from fastapi import status
import aiofiles 
from src.observability.logger import get_logger
from src.api.controllers.ProjectController import projectController
import os 
from src.config.settings import get_settings , settings
from  src.api.controllers.DataController import DataController

from src.validators.data_rag import processRecquest
from src.api.controllers.ProcessController import ProcessController

router=APIRouter(prefix="/RAG-DATA", tags=["RAG-DATA"])

logger = get_logger("routes.RAG-DATA")

@router.post ("/upload/{project_id}")
async def upload_data(project_id: str ,File: UploadFile ,
                      app_settings : settings = Depends(get_settings)):


        # validation the file and the size 
    is_valid= DataController().validate_uploaded_file(file=File)


    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal":"the file not valid"
            }
        )
    file_path , file_id=DataController().generate_unique_filepath(orig_file_name=File.filename,project_id=project_id)
    
    try:
        async with aiofiles.open(
            file_path,"wb"
        )as f:
            
            while chunk:=await File.read(
            app_settings.FILE_DEFAULT_CHUNK_SIZE
        ):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"error:{e}")
        return JSONResponse(
         status_code=status.HTTP_400_BAD_REQUEST,
         content={"signal": "can't uploud the file "}
            )
    return JSONResponse(
         status_code=status.HTTP_200_OK,
         content={"signal": "file uploaded successfully","path": file_path,"file_id":file_id}
            )



@router.post ("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: processRecquest):
    file_id=process_request.file_id
    chunk_size=process_request.chunk_size
    overlap_size=process_request.overlap_size


    process_controller=ProcessController(project_id=project_id)
    file_content=process_controller.get_file_content(file_id=file_id)
    file_chunk=process_controller.process_file_content(file_content=file_content,
                                                        chunk_size=chunk_size, 
                                                        overlap_size=overlap_size, 
                                                        file_id=file_id)
    if file_chunk is None or len (file_chunk)==0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": "can't process the file content"}
        )

    serialized_chunks = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
        }
        for chunk in file_chunk
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={"signal": "file processed successfully","file_chunk": serialized_chunks}
    )


