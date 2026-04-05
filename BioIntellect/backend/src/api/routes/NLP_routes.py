import asyncio
import json
import os
import uuid
from typing import Any
from typing import cast

from fastapi import (
	APIRouter,
	Depends,
	File,
	Form,
	HTTPException,
	Query,
	Request,
	UploadFile,
	status,
)
from fastapi.responses import StreamingResponse

from src.api.controllers.NLPController import NLPController
from src.api.controllers.ProcessController import ProcessController
from src.config.settings import get_settings
from src.observability.logger import get_logger
from src.repositories.clinical_repository import ClinicalRepository
from src.repositories.llm_repository import LLMRepository
from src.repositories.user_repository import UserRepository
from src.security.auth_middleware import (
	Permission,
	get_current_user,
	require_permission,
)
from src.stores.llm.LLMEnums import DocumentTypeEnums
from src.stores.llm.LLMProviderFactory import LLMProviderFactory
from src.validators.nlp_dto import PushRequest, SearchRequest

router = APIRouter(prefix="/nlp", tags=["nlp"])

logger = get_logger("routes.nlp")

CHAT_LLM_DEPENDENCY = Depends(require_permission(Permission.CHAT_LLM))
UPLOAD_FILES_DEPENDENCY = Depends(require_permission(Permission.UPLOAD_FILES))
CURRENT_USER_DEPENDENCY = Depends(get_current_user)

SUPPORTED_MODEL_BACKENDS = {"cohere", "openai", "medmo", "phi_qa"}
CHAT_UPLOAD_PREFIX = "chat_upload::"
CHAT_UPLOAD_DIR = os.path.join("chat_uploads", "attachments")
DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".dcm", ".nii", ".nii.gz"}
ATTACHMENT_FILES_FORM = File(...)
PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
DEFAULT_MEDMO_MODEL_CANDIDATES = [
	os.path.join(PROJECT_ROOT, "AI", "fintune", "medmo_8B", "MedMO-8B-Next"),
	os.path.join(PROJECT_ROOT, "AI", "fintune", "medmo_8B"),
]
DEFAULT_PHI_QA_MODEL_CANDIDATES = [
	os.path.join(PROJECT_ROOT, "AI", "fintune", "fintuned_QA_model", "phi_medical_full_merged_16bit_QA"),
	os.path.join(PROJECT_ROOT, "AI", "fintune", "fintuned_QA_model", "phi-medical-af-qa-lora-r32_checkpoint"),
	os.path.join(PROJECT_ROOT, "AI", "fintune", "fintuned_QA_model"),
]


def _safe_filename(filename: str) -> str:
	base = os.path.basename(filename or "")
	return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in base).strip("._")


def _detect_attachment_kind(filename: str) -> str | None:
	name = (filename or "").strip().lower()
	if name.endswith(".nii.gz"):
		return "image"
	ext = os.path.splitext(name)[1]
	if ext in DOCUMENT_EXTENSIONS:
		return "document"
	if ext in IMAGE_EXTENSIONS:
		return "image"
	return None


def _upload_id(relative_path: str) -> str:
	return f"{CHAT_UPLOAD_PREFIX}{relative_path}"


def _extract_relative_upload_path(identifier: str) -> str | None:
	value = str(identifier or "").strip()
	if not value.startswith(CHAT_UPLOAD_PREFIX):
		return None
	relative_path = value[len(CHAT_UPLOAD_PREFIX):].strip().replace("\\", "/")
	if not relative_path:
		return None
	return relative_path


def _first_existing_dir(paths: list[str | None]) -> str | None:
	for candidate in paths:
		resolved = os.path.realpath(os.path.expandvars(os.path.expanduser(str(candidate or "").strip())))
		if resolved and os.path.isdir(resolved):
			return resolved
	return None


def _detect_local_model_path(settings, backend: str) -> str | None:
	if backend == "medmo":
		return _first_existing_dir([
			settings.MEDMO_MODEL_PATH,
			settings.MEDMO_GENERATION_MODEL_ID,
			*DEFAULT_MEDMO_MODEL_CANDIDATES,
		])
	if backend == "phi_qa":
		return _first_existing_dir([
			settings.PHI_QA_MODEL_PATH,
			settings.PHI_QA_GENERATION_MODEL_ID,
			*DEFAULT_PHI_QA_MODEL_CANDIDATES,
		])
	return None


def _resolve_backend_model_id(settings, backend: str) -> str | None:
	if backend == "openai":
		return settings.OPENAI_GENERATION_MODEL_ID or settings.GENERATION_MODEL_ID or "gpt-4o-mini"
	if backend == "cohere":
		return settings.COHERE_GENERATION_MODEL_ID or settings.GENERATION_MODEL_ID or "command-r-plus"
	if backend == "medmo":
		return settings.MEDMO_GENERATION_MODEL_ID or settings.MEDMO_MODEL_PATH or _detect_local_model_path(settings, "medmo")
	if backend == "phi_qa":
		return settings.PHI_QA_GENERATION_MODEL_ID or settings.PHI_QA_MODEL_PATH or _detect_local_model_path(settings, "phi_qa")
	return settings.GENERATION_MODEL_ID


def _is_backend_enabled(settings, backend: str) -> bool:
	if backend == "openai":
		return bool(settings.OPENAI_API_KEY)
	if backend == "cohere":
		return bool(settings.COHERE_API_KEY)
	if backend == "medmo":
		return bool(_detect_local_model_path(settings, "medmo"))
	if backend == "phi_qa":
		return bool(_detect_local_model_path(settings, "phi_qa"))
	return False


def _model_catalog() -> list[dict[str, Any]]:
	settings = get_settings()
	return [
		{
			"backend": "cohere",
			"label": "Cohere Clinical",
			"enabled": _is_backend_enabled(settings, "cohere"),
			"model_id": _resolve_backend_model_id(settings, "cohere"),
		},
		{
			"backend": "phi_qa",
			"label": "Phi Medical QA",
			"enabled": _is_backend_enabled(settings, "phi_qa"),
			"model_id": _resolve_backend_model_id(settings, "phi_qa"),
		},
		{
			"backend": "medmo",
			"label": "MedMO Clinical",
			"enabled": _is_backend_enabled(settings, "medmo"),
			"model_id": _resolve_backend_model_id(settings, "medmo"),
		},
		{
			"backend": "openai",
			"label": "OpenAI Clinical",
			"enabled": _is_backend_enabled(settings, "openai"),
			"model_id": _resolve_backend_model_id(settings, "openai"),
		},
	]


def _resolve_generation_client(request: Request, requested_backend: str | None):
	settings = get_settings()
	default_backend = settings.GENERATION_BACKEND
	backend = str(requested_backend or default_backend).strip().lower()
	if backend not in SUPPORTED_MODEL_BACKENDS:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported model backend")
	if not _is_backend_enabled(settings, backend):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Selected model backend '{backend}' is not configured")

	if not hasattr(request.app.state, "generation_clients") or request.app.state.generation_clients is None:
		request.app.state.generation_clients = {}
	cache = request.app.state.generation_clients

	if backend == default_backend and getattr(request.app.state, "generation_client", None) is not None:
		client = request.app.state.generation_client
		cache[backend] = client
	elif backend in cache:
		client = cache[backend]
	else:
		local_model_path = _detect_local_model_path(settings, backend)
		default_input_max_characters = cast(int, settings.INPUT_DEFAULT_MAX_CHARACTERS or 1000)
		default_output_max_tokens = cast(int, settings.INPUT_DEFAULT_MAX_TOKENS or 1000)
		default_temp = cast(float, settings.INPUT_DEFAULT_TEMPERATURE or 0.1)
		try:
			if backend == "medmo" and local_model_path and not settings.MEDMO_MODEL_PATH:
				from src.stores.llm.providers.MedMOProvider import MedMOProvider

				client = MedMOProvider(
					model_path=local_model_path,
					default_input_max_characters=default_input_max_characters,
					default_output_max_tokens=default_output_max_tokens,
					default_temp=default_temp,
					offload_folder=settings.MEDMO_OFFLOAD_FOLDER,
				)
			elif backend == "phi_qa" and local_model_path and not settings.PHI_QA_MODEL_PATH:
				from src.stores.llm.providers.PhiQAProvider import PhiQAProvider

				client = PhiQAProvider(
					model_path=local_model_path,
					default_input_max_characters=default_input_max_characters,
					default_output_max_tokens=default_output_max_tokens,
					default_temp=default_temp,
				)
			else:
				factory = LLMProviderFactory(settings)
				client = factory.create(backend=backend)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to initialize backend '{backend}': {str(exc)}") from exc
		cache[backend] = client

	model_id = _resolve_backend_model_id(settings, backend)
	if model_id and hasattr(client, "set_generation_model"):
		try:
			client.set_generation_model(model_id=model_id)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to set model for backend '{backend}': {str(exc)}") from exc

	return client, backend, model_id


def _resolve_uploaded_image_path(project_id: str, image_ids: list[str]) -> str | None:
	if not image_ids:
		return None
	process_controller = ProcessController(project_id=project_id)
	base_dir = os.path.realpath(process_controller.project_path)
	for identifier in image_ids:
		relative_path = _extract_relative_upload_path(str(identifier))
		if not relative_path:
			continue
		full_path = os.path.realpath(os.path.join(base_dir, relative_path))
		if not full_path.startswith(base_dir + os.sep):
			continue
		if os.path.isfile(full_path):
			return full_path
	return None


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


async def _build_patient_context(patient_id: str) -> dict[str, Any] | None:
	repo = UserRepository()
	clinical_repo = ClinicalRepository()

	patient, history = await asyncio.gather(
		repo.get_patient(patient_id),
		clinical_repo.get_patient_history(patient_id),
		return_exceptions=True,
	)

	if isinstance(patient, Exception) or not patient:
		return None

	history_payload: dict[str, Any] = {
		"recent_cases": [],
		"recent_ecg_results": [],
		"recent_mri_results": [],
	}
	if not isinstance(history, Exception) and history:
		history_payload = {
			"recent_cases": list(history.get("cases") or [])[:20],
			"recent_ecg_results": list(history.get("ecg_results") or [])[:10],
			"recent_mri_results": list(history.get("mri_results") or [])[:10],
		}

	return {
		"id": patient.get("id"),
		"mrn": patient.get("mrn") or patient.get("medical_record_number"),
		"first_name": patient.get("first_name"),
		"last_name": patient.get("last_name"),
		"gender": patient.get("gender"),
		"date_of_birth": patient.get("date_of_birth"),
		"primary_doctor_id": patient.get("primary_doctor_id"),
		"hospital_id": patient.get("hospital_id"),
		"medical_history": history_payload,
	}


def _build_message_metadata(
	project_id: str,
	search_request: SearchRequest,
	language: str,
	extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
	metadata: dict[str, Any] = {
		"project_id": project_id,
		"language": language,
	}
	if search_request.context_file_ids:
		metadata["context_file_ids"] = search_request.context_file_ids
	if search_request.image_file_ids:
		metadata["image_file_ids"] = search_request.image_file_ids
	if search_request.model_backend:
		metadata["model_backend"] = search_request.model_backend
	if extra:
		metadata.update(extra)
	return metadata


def _format_patient_context_for_prompt(patient_context: dict[str, Any] | None) -> str:
	if not isinstance(patient_context, dict):
		return ""

	medical_history = patient_context.get("medical_history") or {}
	recent_cases = list(medical_history.get("recent_cases") or [])[:10]
	recent_ecg = list(medical_history.get("recent_ecg_results") or [])[:10]
	recent_mri = list(medical_history.get("recent_mri_results") or [])[:10]

	summary_payload = {
		"patient": {
			"id": patient_context.get("id"),
			"mrn": patient_context.get("mrn"),
			"first_name": patient_context.get("first_name"),
			"last_name": patient_context.get("last_name"),
			"gender": patient_context.get("gender"),
			"date_of_birth": patient_context.get("date_of_birth"),
		},
		"medical_history": {
			"recent_cases": recent_cases,
			"recent_ecg_results": recent_ecg,
			"recent_mri_results": recent_mri,
		},
	}

	return json.dumps(summary_payload, ensure_ascii=False)


def _augment_question_with_patient_context(question: str, patient_context: dict[str, Any] | None) -> str:
	context_blob = _format_patient_context_for_prompt(patient_context)
	if not context_blob:
		return question

	return (
		"Use the following patient clinical context to answer accurately and specifically. "
		"If a field is missing, state that clearly instead of guessing.\n"
		f"PATIENT_CONTEXT_JSON:\n{context_blob}\n\n"
		f"USER_QUESTION:\n{question}"
	)


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

	conversation_metadata: dict[str, Any] = {
		"project_id": project_id,
		"created_via": "nlp_routes",
	}
	if role != "patient":
		try:
			patient_context = await _build_patient_context(patient_id)
			if patient_context:
				conversation_metadata["patient_context"] = patient_context
				conversation_metadata["patient_context_loaded"] = True
		except Exception as exc:
			logger.warning(f"Failed to preload patient context for conversation: {str(exc)}")

	conversation = await repo.create(
		{
			"title": (search_request.title or "Medical Consultation").strip() or "Medical Consultation",
			"conversation_type": conversation_type,
			"patient_id": patient_id,
			"doctor_id": doctor_id,
			"hospital_id": hospital_id,
			"metadata": conversation_metadata,
		}
	)
	if not conversation:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to create conversation")
	return conversation

@router.post("/index/push/{project_id}", dependencies=[UPLOAD_FILES_DEPENDENCY])
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

@router.get("/index/info/{project_id}", dependencies=[CHAT_LLM_DEPENDENCY])
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
@router.post("/index/search/{project_id}", dependencies=[CHAT_LLM_DEPENDENCY])
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


@router.get(
	"/models",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def list_chat_models():
	settings = get_settings()
	return {
		"default_backend": settings.GENERATION_BACKEND,
		"models": _model_catalog(),
	}


@router.post(
	"/chats/{project_id}/attachments",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def upload_chat_attachments(
	request: Request,
	project_id: str,
	files: list[UploadFile] = ATTACHMENT_FILES_FORM,
	patient_id: str | None = Form(default=None),
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
	if not files:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

	role = str(user.get("role") or "").strip().lower()
	resolved_patient_id = str(patient_id or "").strip() if role != "patient" else _resolve_profile_id(user)
	if role != "patient" and not resolved_patient_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required")

	process_controller = ProcessController(project_id=project_id)
	base_dir = os.path.realpath(process_controller.project_path)
	upload_dir = os.path.realpath(os.path.join(base_dir, CHAT_UPLOAD_DIR))
	if not upload_dir.startswith(base_dir + os.sep):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload path")
	os.makedirs(upload_dir, exist_ok=True)

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	generation_client = getattr(request.app.state, "generation_client", None)
	template_parser = getattr(request.app.state, "template_parser", None)

	indexed_documents: list[dict[str, str]] = []
	uploaded_images: list[dict[str, str]] = []
	rejected_files: list[dict[str, str]] = []

	for upload in files:
		filename = _safe_filename(upload.filename or "")
		kind = _detect_attachment_kind(filename)
		if not filename or kind is None:
			rejected_files.append({"file": upload.filename or "unknown", "reason": "Unsupported file type"})
			continue

		relative_path = os.path.join(CHAT_UPLOAD_DIR, f"{uuid.uuid4().hex}_{filename}").replace("\\", "/")
		full_path = os.path.realpath(os.path.join(base_dir, relative_path))
		if not full_path.startswith(base_dir + os.sep):
			rejected_files.append({"file": upload.filename or "unknown", "reason": "Invalid file path"})
			continue

		content = await upload.read()
		if not content:
			rejected_files.append({"file": upload.filename or "unknown", "reason": "Empty file"})
			continue

		with open(full_path, "wb") as handle:
			handle.write(content)

		upload_identifier = _upload_id(relative_path)
		label = f"{filename} (uploaded)"

		if kind == "image":
			uploaded_images.append({"id": upload_identifier, "label": label})
			continue

		if vectordb_client is None or embedding_client is None or generation_client is None or template_parser is None:
			indexed_documents.append({"id": upload_identifier, "label": f"{label} • not indexed"})
			continue

		try:
			file_content = process_controller.get_file_content(file_id=relative_path)
			chunks = process_controller.process_file_content(file_content=file_content, file_id=relative_path)
			if not chunks:
				raise ValueError("No chunks generated")

			texts = [chunk.page_content for chunk in chunks]
			vectors = embedding_client.embed_text(text=texts, document_type=DocumentTypeEnums.document.value)
			if any(vector is None or len(vector) == 0 for vector in vectors):
				raise ValueError("Failed to generate embeddings")

			metadata = []
			for chunk in chunks:
				chunk_metadata = dict(chunk.metadata or {})
				chunk_metadata.update({
					"chat_attachment": True,
					"patient_id": resolved_patient_id,
					"source_file_id": upload_identifier,
				})
				metadata.append(chunk_metadata)

			nlp_controller = NLPController(
				vectorDB_client=vectordb_client,
				generation_client=generation_client,
				embedding_client=embedding_client,
				template_parser=template_parser,
			)
			nlp_controller.index_into_vector_db(
				project_id=project_id,
				texts=texts,
				vectors=vectors,
				metadata=metadata,
				do_reset=False,
			)
			indexed_documents.append({"id": upload_identifier, "label": label})
		except Exception as exc:
			rejected_files.append({"file": upload.filename or "unknown", "reason": f"Indexing failed: {str(exc)}"})

	return {
		"documents": indexed_documents,
		"images": uploaded_images,
		"rejected": rejected_files,
	}


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
	language = search_request.language if search_request.language is not None else "en"
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
	if not search_request.text or not search_request.text.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

	vectordb_client = getattr(request.app.state, "vectordb_client", None)
	embedding_client = getattr(request.app.state, "embedding_client", None)
	template_parser = getattr(request.app.state, "template_parser", None)
	if vectordb_client is None or embedding_client is None or template_parser is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	generation_client, resolved_backend, resolved_model_id = _resolve_generation_client(
		request=request,
		requested_backend=search_request.model_backend,
	)
	search_request.model_backend = resolved_backend
	image_path = _resolve_uploaded_image_path(project_id=project_id, image_ids=search_request.image_file_ids)

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=generation_client,
		embedding_client=embedding_client,
		template_parser=template_parser,
	)
	
	# Load patient context for augmentation (same as streaming endpoint)
	patient_context = None
	patient_id_for_context = str(search_request.patient_id or "").strip()
	if patient_id_for_context:
		try:
			patient_context = await _build_patient_context(patient_id_for_context)
		except Exception as exc:
			logger.warning(f"Failed to fetch patient context for {patient_id_for_context}: {str(exc)}")
	
	question_for_model = _augment_question_with_patient_context(search_request.text, patient_context)
	
	try:
		answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
			project_id=project_id,
			question=question_for_model,
			limit=search_request.top_k,
			chat_history=search_request.chat_history,
			language=language,
			image_path=image_path,
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
	
	try:
		user_message = await repo.create_message(
			{
				"conversation_id": conversation_id,
				"sender_type": sender_type,
				"sender_id": sender_id,
				"message_content": search_request.text,
				"message_type": "medical_query",
				"metadata": _build_message_metadata(project_id, search_request, language),
			}
		)
		if user_message is None:
			logger.warning(f"Failed to create user message for conversation {conversation_id}")
	except Exception as exc:
		logger.warning(f"Error creating user message: {str(exc)}")
		user_message = None
	
	try:
		assistant_message = await repo.create_message(
			{
				"conversation_id": conversation_id,
				"sender_type": "llm",
				"message_content": answer,
				"message_type": "text",
				"metadata": _build_message_metadata(
					project_id,
					search_request,
					language,
					extra={
						"full_prompt": full_prompt,
						"model_backend": resolved_backend,
						"model_id": resolved_model_id,
					},
				),
			}
		)
		if assistant_message is None:
			logger.warning(f"Failed to create assistant message for conversation {conversation_id}")
	except Exception as exc:
		logger.warning(f"Error creating assistant message: {str(exc)}")
		assistant_message = None

	return {
		"conversation_id": conversation_id,
		"answer": answer,
		"full_prompt": full_prompt,
		"chat_history": chat_history,
		"user_message": user_message,
		"assistant_message": assistant_message,
	}


def _format_sse(event_name: str, payload: dict) -> str:
	return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


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
	embedding_client = getattr(request.app.state, "embedding_client", None)
	template_parser = getattr(request.app.state, "template_parser", None)
	if vectordb_client is None or embedding_client is None or template_parser is None:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Required NLP clients are not initialized")

	generation_client, resolved_backend, resolved_model_id = _resolve_generation_client(
		request=request,
		requested_backend=search_request.model_backend,
	)
	search_request.model_backend = resolved_backend
	image_path = _resolve_uploaded_image_path(project_id=project_id, image_ids=search_request.image_file_ids)

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
		conversation_metadata = conversation.get("metadata") or {}
		patient_id_for_context = str(
			conversation.get("patient_id")
			or search_request.patient_id
			or ""
		).strip()
		patient_context = None
		if patient_id_for_context:
			try:
				# Always fetch fresh patient history from Supabase for each streamed answer.
				patient_context = await _build_patient_context(patient_id_for_context)
			except Exception as exc:
				logger.warning(
					f"Failed to fetch live patient context for {patient_id_for_context}: {str(exc)}"
				)

		if not patient_context and isinstance(conversation_metadata, dict):
			patient_context = conversation_metadata.get("patient_context")

		question_for_model = _augment_question_with_patient_context(
			search_request.text,
			patient_context,
		)
		yield _format_sse("start", {"project_id": project_id, "conversation_id": conversation_id})

		try:
			await repo.create_message(
				{
					"conversation_id": conversation_id,
					"sender_type": _sender_type_for_role(user),
					"sender_id": _resolve_profile_id(user),
					"message_content": search_request.text,
					"message_type": "medical_query",
					"metadata": _build_message_metadata(
						project_id,
						search_request,
						search_request.language or "en",
					),
				}
			)
		except Exception as exc:
			yield _format_sse("error", {"message": f"Failed to save user message: {str(exc)}"})
			return

		try:
			# Emit an immediate progress token so clients do not appear frozen
			# while the model prepares the first real chunk.
			yield _format_sse("token", {"text": "..."})
			await asyncio.sleep(0)

			answer, _, _ = await asyncio.to_thread(
				nlp_controller.answer_rag_question,
				project_id=project_id,
				question=question_for_model,
				limit=search_request.top_k,
				chat_history=search_request.chat_history,
				language=search_request.language,
				image_path=image_path,
			)
			answer = str(answer or "")
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
					"metadata": _build_message_metadata(
						project_id,
						search_request,
						search_request.language or "en",
						extra={
							"model_backend": resolved_backend,
							"model_id": resolved_model_id,
						},
					),
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


@router.get(
	"/conversations/count",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def get_conversation_count(
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	"""Return the active conversation count for the current doctor."""
	role = str(user.get("role") or "").strip().lower()
	profile_id = _resolve_profile_id(user)
	settings = get_settings()
	max_limit = settings.MAX_CONVERSATIONS_PER_DOCTOR

	if role == "patient":
		return {"success": True, "data": {"count": 0, "max_limit": max_limit, "is_at_limit": False}}

	repo = LLMRepository()
	count = await repo.count_active_conversations(profile_id)
	return {
		"success": True,
		"data": {
			"count": count,
			"max_limit": max_limit,
			"is_at_limit": count >= max_limit,
		},
	}


@router.patch(
	"/chats/{project_id}/conversations/{conversation_id}/archive",
	dependencies=[CHAT_LLM_DEPENDENCY],
)
async def archive_rag_conversation(
	project_id: str,
	conversation_id: str,
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
	reason: str | None = Query(default=None),
):
	"""Archive a conversation so it no longer counts against the active limit."""
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	repo = LLMRepository()
	await _assert_conversation_access(
		repo=repo,
		conversation_id=conversation_id,
		project_id=project_id,
		user=user,
	)

	profile_id = _resolve_profile_id(user)
	success = await repo.archive_conversation(
		conversation_id=conversation_id,
		user_id=profile_id,
		reason=reason,
	)
	if not success:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to archive conversation")

	return {"success": True, "message": "Conversation archived successfully"}
