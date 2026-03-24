from fastapi import APIRouter, HTTPException, Request, status

from src.api.controllers.NLPController import NLPController
from src.api.controllers.ProcessController import ProcessController
from src.observability.logger import get_logger
from src.validators.nlp_dto import PushRequest, SearchRequest

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
	try:
		vectors = embedding_client.embed_text(text=texts)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Embedding provider rate-limited or failed: {str(exc)}") from exc
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

@router.get ("/index/info/{project_id}")
async def get_index_info(request: Request, project_id: str):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	if vectordb_client is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vector database client is not initialized")
	
	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=None,
		embedding_client=None,
	)

	try:
		collection_info = nlp_controller.get_vector_db_collection_info(project_id=project_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

	if collection_info is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No vector database collection found for project {project_id}")
	return {"collection_info": collection_info}
@router.post ("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
	query = search_request.text
	top_k = search_request.top_k
	limit = search_request.limit if search_request.limit is not None else top_k
	if not query.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	if vectordb_client is None or embedding_client is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=None,
		embedding_client=embedding_client,
	)

	try:
		search_results = nlp_controller.search_vector_db_collection(
			project_id=project_id,
			text=query,
			limit=limit,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Vector database search failed: {str(exc)}") from exc

	return {"results": search_results}