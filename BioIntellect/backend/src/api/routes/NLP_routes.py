import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from src.api.controllers.NLPController import NLPController
from src.api.controllers.ProcessController import ProcessController
from src.observability.logger import get_logger
from src.repositories.llm_repository import LLMRepository
from src.security.auth_middleware import (
	Permission,
	get_current_user,
	require_permission,
)
from src.stores.llm.LLMEnums import DocumentTypeEnums
from src.validators.nlp_dto import PushRequest, SearchRequest

router=APIRouter(prefix="/nlp", tags=["nlp"])

logger = get_logger("routes.nlp")

CHAT_LLM_DEPENDENCY = Depends(require_permission(Permission.CHAT_LLM))
CURRENT_USER_DEPENDENCY = Depends(get_current_user)


def _resolve_profile_id(user: dict[str, Any]) -> str:
	profile_id = str(user.get("profile_id") or user.get("id") or "").strip()
	if not profile_id:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user context")
	return profile_id


def _is_privileged_user(user: dict[str, Any]) -> bool:
	role = str(user.get("role") or "").strip().lower()
	return role in {"admin", "super_admin"}


def _sender_type_for_role(user: dict[str, Any]) -> str:
	role = str(user.get("role") or "").strip().lower()
	return "patient" if role == "patient" else "doctor"


def _conversation_project_id(conversation: dict[str, Any]) -> str | None:
	metadata = conversation.get("metadata") or {}
	if isinstance(metadata, dict):
		value = metadata.get("project_id")
		return str(value) if value is not None else None
	return None


async def _assert_conversation_access(
	repo: LLMRepository,
	conversation_id: str,
	project_id: str,
	user: dict[str, Any],
) -> dict[str, Any]:
	conversation = await repo.get_conversation(conversation_id)
	if not conversation:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

	conversation_project_id = _conversation_project_id(conversation)
	if conversation_project_id != project_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conversation does not belong to this project")

	if _is_privileged_user(user):
		return conversation

	profile_id = _resolve_profile_id(user)
	role = str(user.get("role") or "").strip().lower()
	if role == "patient" and conversation.get("patient_id") != profile_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
	if role != "patient" and conversation.get("doctor_id") != profile_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

	return conversation


async def _resolve_or_create_conversation(
	repo: LLMRepository,
	project_id: str,
	search_request: SearchRequest,
	user: dict[str, Any],
) -> dict[str, Any]:
	if search_request.conversation_id:
		return await _assert_conversation_access(
			repo=repo,
			conversation_id=search_request.conversation_id,
			project_id=project_id,
			user=user,
		)

	profile_id = _resolve_profile_id(user)
	role = str(user.get("role") or "").strip().lower()
	hospital_id = str(user.get("hospital_id") or "").strip()
	if not hospital_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hospital context is required")

	if role == "patient":
		patient_id = profile_id
		doctor_id = None
		conversation_type = "patient_llm"
	else:
		patient_id = (search_request.patient_id or "").strip()
		if not patient_id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required for non-patient users")
		doctor_id = profile_id
		conversation_type = "doctor_llm"

	conversation = await repo.create(
		{
			"title": (search_request.title or "Medical Consultation").strip() or "Medical Consultation",
			"conversation_type": conversation_type,
			"patient_id": patient_id,
			"doctor_id": doctor_id,
			"hospital_id": hospital_id,
			"metadata": {"project_id": project_id, "created_via": "nlp_routes"},
		}
	)
	if not conversation:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to create conversation")
	return conversation

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
		vectors = embedding_client.embed_text(
			text=texts,
			document_type=DocumentTypeEnums.document.value,
		)
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
		template_parser=getattr(request.app.state, "template_parser", None),
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
		template_parser=getattr(request.app.state, "template_parser", None),
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
		template_parser=getattr(request.app.state, "template_parser", None),
	)

	try:
		search_results = nlp_controller.search_vector_db_collection(
			project_id=project_id,
			text=query,
			limit=search_request.top_k,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Vector database search failed: {str(exc)}") from exc

	return {"results": search_results}


@router.post(
	"/chats/{project_id}/conversations",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def create_rag_conversation(
	project_id: str,
	payload: dict[str, Any],
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	profile_id = _resolve_profile_id(user)
	role = str(user.get("role") or "").strip().lower()
	hospital_id = str(user.get("hospital_id") or payload.get("hospital_id") or "").strip()
	if not hospital_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hospital_id is required")

	if role == "patient":
		patient_id = profile_id
		doctor_id = None
		conversation_type = "patient_llm"
	else:
		patient_id = str(payload.get("patient_id") or "").strip()
		if not patient_id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required")
		doctor_id = profile_id
		conversation_type = str(payload.get("conversation_type") or "doctor_llm")

	repo = LLMRepository()
	conversation = await repo.create(
		{
			"title": str(payload.get("title") or "Medical Consultation").strip() or "Medical Consultation",
			"conversation_type": conversation_type,
			"patient_id": patient_id,
			"doctor_id": doctor_id,
			"hospital_id": hospital_id,
			"metadata": {"project_id": project_id, "created_via": "nlp_routes"},
		}
	)
	if not conversation:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to create conversation")

	return {"conversation": conversation}


@router.get(
	"/chats/{project_id}/conversations",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def list_rag_conversations(
	project_id: str,
	limit: int = Query(50, ge=1, le=100),
	offset: int = Query(0, ge=0),
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	repo = LLMRepository()
	role = str(user.get("role") or "").strip().lower()
	profile_id = _resolve_profile_id(user)
	filters: dict[str, Any] = {"is_archived": False}
	if role == "patient":
		filters["patient_id"] = profile_id
	elif role == "doctor":
		filters["doctor_id"] = profile_id
	elif not _is_privileged_user(user):
		filters["user_id"] = profile_id

	conversations = await repo.list_conversations(filters, limit, offset)
	filtered_conversations = [
		conversation
		for conversation in conversations
		if _conversation_project_id(conversation) == project_id
	]
	return {"conversations": filtered_conversations}


@router.get(
	"/chats/{project_id}/conversations/{conversation_id}/messages",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def list_rag_messages(
	project_id: str,
	conversation_id: str,
	limit: int = Query(100, ge=1, le=200),
	offset: int = Query(0, ge=0),
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	repo = LLMRepository()
	await _assert_conversation_access(
		repo=repo,
		conversation_id=conversation_id,
		project_id=project_id,
		user=user,
	)
	messages = await repo.list_messages(
		{"conversation_id": conversation_id, "is_deleted": False},
		limit,
		offset,
	)
	return {"messages": messages}


@router.post (
	"/index/answer/{project_id}",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def answer_rag(
	request: Request,
	project_id: str,
	search_request: SearchRequest,
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
	if not search_request.text or not search_request.text.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	generation_client = getattr(request.app.state, "generation_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	template_parser = getattr(request.app.state, "template_parser", None)
	if vectordb_client is None or generation_client is None or embedding_client is None or template_parser is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=generation_client,
		embedding_client=embedding_client,
		template_parser=template_parser,
	)
	try:
		answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
			project_id=project_id,
			question=search_request.text,
			limit=search_request.top_k,
			chat_history=search_request.chat_history,
			language=search_request.language,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to answer RAG question: {str(exc)}") from exc

	if not answer :
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to generate answer for the question")

	repo = LLMRepository()
	conversation = await _resolve_or_create_conversation(
		repo=repo,
		project_id=project_id,
		search_request=search_request,
		user=user,
	)
	conversation_id = str(conversation.get("id"))
	sender_type = _sender_type_for_role(user)
	sender_id = _resolve_profile_id(user)
	user_message = await repo.create_message(
		{
			"conversation_id": conversation_id,
			"sender_type": sender_type,
			"sender_id": sender_id,
			"message_content": search_request.text,
			"message_type": "medical_query",
			"metadata": {"project_id": project_id, "language": search_request.language},
		}
	)
	assistant_message = await repo.create_message(
		{
			"conversation_id": conversation_id,
			"sender_type": "llm",
			"message_content": answer,
			"message_type": "text",
			"metadata": {"project_id": project_id, "full_prompt": full_prompt},
		}
	)

	return {
		"conversation_id": conversation_id,
		"answer": answer,
		"full_prompt": full_prompt,
		"chat_history": chat_history,
		"user_message": user_message,
		"assistant_message": assistant_message,
	}


def _format_sse(event_name: str, payload: dict) -> str:
	return f"event: {event_name}\\ndata: {json.dumps(payload, ensure_ascii=False)}\\n\\n"


def _chunk_text(text: str, chunk_size: int = 24):
	for index in range(0, len(text), chunk_size):
		yield text[index : index + chunk_size]


@router.post(
	"/index/answer-stream/{project_id}",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def answer_rag_stream(
	request: Request,
	project_id: str,
	search_request: SearchRequest,
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
	if not search_request.text or not search_request.text.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	generation_client = getattr(request.app.state, "generation_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	template_parser = getattr(request.app.state, "template_parser", None)
	if vectordb_client is None or generation_client is None or embedding_client is None or template_parser is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=generation_client,
		embedding_client=embedding_client,
		template_parser=template_parser,
	)
	repo = LLMRepository()

	async def event_generator():
		try:
			conversation = await _resolve_or_create_conversation(
				repo=repo,
				project_id=project_id,
				search_request=search_request,
				user=user,
			)
		except HTTPException as exc:
			yield _format_sse("error", {"message": str(exc.detail)})
			return

		conversation_id = str(conversation.get("id"))
		yield _format_sse("start", {"project_id": project_id, "conversation_id": conversation_id})

		try:
			await repo.create_message(
				{
					"conversation_id": conversation_id,
					"sender_type": _sender_type_for_role(user),
					"sender_id": _resolve_profile_id(user),
					"message_content": search_request.text,
					"message_type": "medical_query",
					"metadata": {"project_id": project_id, "language": search_request.language},
				}
			)
		except Exception as exc:
			yield _format_sse("error", {"message": f"Failed to save user message: {str(exc)}"})
			return

		try:
			answer, _, _ = nlp_controller.answer_rag_question(
				project_id=project_id,
				question=search_request.text,
				limit=search_request.top_k,
				chat_history=search_request.chat_history,
				language=search_request.language,
			)
		except ValueError as exc:
			yield _format_sse("error", {"message": str(exc)})
			return
		except Exception as exc:
			yield _format_sse("error", {"message": f"Failed to answer RAG question: {str(exc)}"})
			return

		for chunk in _chunk_text(answer):
			yield _format_sse("token", {"text": chunk})
			await asyncio.sleep(0)

		try:
			assistant_message = await repo.create_message(
				{
					"conversation_id": conversation_id,
					"sender_type": "llm",
					"message_content": answer,
					"message_type": "text",
					"metadata": {"project_id": project_id},
				}
			)
		except Exception as exc:
			yield _format_sse("error", {"message": f"Failed to save assistant message: {str(exc)}"})
			return

		yield _format_sse("done", {"answer": answer, "conversation_id": conversation_id, "assistant_message": assistant_message})

	return StreamingResponse(
		event_generator(),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"Connection": "keep-alive",
			"X-Accel-Buffering": "no",
		},
	)
