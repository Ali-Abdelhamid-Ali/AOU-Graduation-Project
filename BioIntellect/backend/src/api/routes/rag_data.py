import os
import uuid
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from src.api.controllers.DataController import DataController
from src.api.controllers.ProcessController import ProcessController
from src.config.settings import get_settings
from src.observability.logger import get_logger
from src.security.auth_middleware import Permission, require_permission
from src.validators.data_rag import processRecquest

router=APIRouter(prefix="/RAG-DATA", tags=["RAG-DATA"])

logger = get_logger("routes.RAG-DATA")

UPLOAD_PERMISSION = Depends(require_permission(Permission.UPLOAD_FILES))


def _validate_project_id(project_id: str) -> str:
    cleaned = (project_id or "").strip()
    try:
        uuid.UUID(cleaned)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id must be a valid UUID",
        ) from exc
    return cleaned

@router.post("/upload/{project_id}", dependencies=[UPLOAD_PERMISSION])
async def upload_data(
    project_id: str,
    File: UploadFile,
    request: Request,
):

    project_id = _validate_project_id(project_id)
    app_settings = request.app.dependency_overrides.get(get_settings, get_settings)()
    max_bytes = app_settings.FILE_MAX_SIZE * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size",
        )


        # validation the file and the size 
    data_controller = DataController()
    data_controller.validate_uploaded_file(file=File)
    filename: str = cast(str, File.filename or "uploaded_file")
    try:
        file_path, file_id = data_controller.generate_unique_filepath(
            orig_file_name=filename,
            project_id=project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    
    try:
        with open(file_path, "wb") as f:
            total_bytes = 0
            while chunk := await File.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Uploaded file exceeds the maximum allowed size",
                    )
                f.write(chunk)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        logger.error(f"error:{e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return JSONResponse(
         status_code=status.HTTP_400_BAD_REQUEST,
         content={"signal": "can't upload the file"}
            )
    return JSONResponse(
         status_code=status.HTTP_200_OK,
         content={"signal": "file uploaded successfully","path": file_path,"file_id":file_id}
            )



@router.post("/process/{project_id}", dependencies=[UPLOAD_PERMISSION])
async def process_endpoint(project_id: str, process_request: processRecquest):
    project_id = _validate_project_id(project_id)
    file_id: str = process_request.file_id
    # None => ProcessController picks adaptive chunk/overlap based on file size.
    chunk_size = int(process_request.chunk_size) if process_request.chunk_size is not None else None
    overlap_size = int(process_request.overlap_size) if process_request.overlap_size is not None else None


    try:
        process_controller=ProcessController(project_id=project_id)
        file_content=process_controller.get_file_content(file_id=file_id)
        file_chunk=process_controller.process_file_content(file_content=file_content,
                                                            chunk_size=chunk_size,
                                                            overlap_size=overlap_size,
                                                            file_id=file_id)
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": str(exc)},
        )
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": str(exc)},
        )
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


