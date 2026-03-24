from fastapi import APIRouter, HTTPException, Request, status

from src.api.controllers.NLPController import NLPController
from src.api.controllers.ProcessController import ProcessController
from src.observability.logger import get_logger
from src.validators.nlp_dto import PushRequest

router=APIRouter(prefix="/nlp", tags=["nlp"])

logger = get_logger("routes.nlp")

@router.post ("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	file_id = push_request.file_id or push_request.metadata.get("file_id", "")
	if not file_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_id is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	generation_client = getattr(request.app.state, "generation_client", None)
	if vectordb_client is None or embedding_client is None or generation_client is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	try:
		process_controller = ProcessController(project_id=project_id)
		file_content = process_controller.get_file_content(file_id=file_id)
		chunks = process_controller.process_file_content(
			file_content=file_content,
			file_id=file_id,
			chunk_size=push_request.chunk_size,
			overlap_size=push_request.overlap_size,
		)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	if not chunks:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no chunks generated")

	texts = [chunk.page_content for chunk in chunks]
	vectors = embedding_client.embed_text(text=texts)
	if any(vector is None or len(vector) == 0 for vector in vectors):
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="failed to generate embeddings for one or more chunks")
	metadata = [chunk.metadata for chunk in chunks]

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=generation_client,
		embedding_client=embedding_client,
	)

	if push_request.do_reset:
		logger.info(f"Reset vector database collection and indexed {len(chunks)} chunks for project {project_id}")
	
	try:
		nlp_controller.index_into_vector_db(
			project_id=project_id,
			texts=texts,
			vectors=vectors,
			metadata=metadata,
			do_reset=bool(push_request.do_reset),
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
	return {"message": f"Successfully indexed {len(chunks)} chunks into vector database for project {project_id}"}

	