from fastapi import APIRouter, Depends
import os

from src.observability.logger import get_logger

from src.config.settings import get_settings, Settings

router=APIRouter(prefix="/RAG", tags=["RAG"])


logger = get_logger("routes.RAG")
@router.get("/welcome")
async def welcome(app_settings : Settings=Depends(get_settings)):

    app_name =app_settings.APP_NAME 
    app_version = app_settings.APP_VERSION

    return{
        "message":"Hello DR.EID",
        "app_name": app_name,
        "app_version": app_version
           }


