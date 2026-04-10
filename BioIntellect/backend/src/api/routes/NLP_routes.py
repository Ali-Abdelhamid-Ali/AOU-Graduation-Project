import asyncio
import os
import time
import uuid
from typing import Any, cast

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
DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}
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


def _local_model_has_weights(model_dir: str | None) -> bool:
	"""Return True only if the directory contains actual model weight files."""
	if not model_dir or not os.path.isdir(model_dir):
		return False
	for fname in os.listdir(model_dir):
		lower = fname.lower()
		if lower.endswith((".bin", ".safetensors", ".pt", ".pth", ".gguf")):
			return True
	return False


def _is_backend_enabled(settings, backend: str) -> bool:
	if backend == "openai":
		return bool(settings.OPENAI_API_KEY)
	if backend == "cohere":
		return bool(settings.COHERE_API_KEY)
	if backend == "medmo":
		return _local_model_has_weights(_detect_local_model_path(settings, "medmo"))
	if backend == "phi_qa":
		return _local_model_has_weights(_detect_local_model_path(settings, "phi_qa"))
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
			if backend == "medmo" and local_model_path:
				from src.stores.llm.providers.MedMOProvider import MedMOProvider

				if not MedMOProvider.is_runtime_available():
					raise RuntimeError(
						"MedMO backend is unavailable because required runtime dependencies are missing "
						"(supported Qwen-VL class + qwen_vl_utils)"
					)

				client = MedMOProvider(
					model_path=local_model_path,
					default_input_max_characters=default_input_max_characters,
					default_output_max_tokens=default_output_max_tokens,
					default_temp=default_temp,
					offload_folder=settings.MEDMO_OFFLOAD_FOLDER,
					force_cpu_only=settings.FORCE_CPU_ONLY,
				)
				if client.model is None:
					raise RuntimeError(f"MedMO model failed to load from '{local_model_path}'")
			elif backend == "phi_qa" and local_model_path:
				from src.stores.llm.providers.PhiQAProvider import PhiQAProvider

				client = PhiQAProvider(
					model_path=local_model_path,
					default_input_max_characters=default_input_max_characters,
					default_output_max_tokens=default_output_max_tokens,
					default_max_input_tokens=default_output_max_tokens,
					default_temp=default_temp,
					force_cpu_only=settings.FORCE_CPU_ONLY,
				)
				if client.model is None:
					raise RuntimeError(f"PhiQA model failed to load from '{local_model_path}'")
			else:
				factory = LLMProviderFactory(settings)
				client = factory.create(backend=backend)
		except HTTPException:
			raise
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


def _is_valid_uuid(value: str | None) -> bool:
	cleaned = str(value or "").strip()
	if not cleaned:
		return False
	try:
		uuid.UUID(cleaned)
		return True
	except Exception:
		return False


def _resolve_rag_project_id(
	*,
	url_project_id: str,
	conversation_project_id: str | None,
) -> str:
	"""Pick the effective project_id to use for vector storage.

	Prefers the per-conversation isolated UUID when provided. Falls back to the
	URL path project_id only when it is itself a valid UUID. Raises a 400 with a
	clear message when neither option is valid — this prevents opaque
	"project_id must be a valid UUID" errors from ProcessController deep in the
	stack and tells the caller exactly what to send.
	"""
	conv_pid = str(conversation_project_id or "").strip()
	if conv_pid:
		if not _is_valid_uuid(conv_pid):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="conversation_project_id must be a valid UUID",
			)
		return conv_pid

	url_pid = str(url_project_id or "").strip()
	if not _is_valid_uuid(url_pid):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=(
				"project_id in the URL must be a valid UUID, or pass a valid "
				"conversation_project_id to scope the request to a conversation"
			),
		)
	return url_pid


def _conversation_project_id(conversation: dict[str, Any]) -> str | None:
	metadata = conversation.get("metadata") or {}
	if isinstance(metadata, dict):
		value = metadata.get("project_id")
		return str(value) if value is not None else None
	return None


def _get_conversation_project_id(conversation: dict[str, Any]) -> str | None:
	"""Return the per-conversation isolated project_id stored in metadata."""
	if conversation.get("conversation_project_id"):
		return str(conversation["conversation_project_id"])
	metadata = conversation.get("metadata") or {}
	if isinstance(metadata, dict):
		value = metadata.get("conversation_project_id")
		return str(value) if value is not None else None
	return None


def _enrich_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
	"""Ensure conversation_project_id is surfaced at top level."""
	result = dict(conversation)
	if not result.get("conversation_project_id"):
		cpid = _get_conversation_project_id(result)
		if cpid:
			result["conversation_project_id"] = cpid
	return result


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


def _summarize_finding(item: dict[str, Any]) -> str:
	"""Reduce an ECG/MRI record to a short natural-language line."""
	if not isinstance(item, dict):
		return ""
	parts: list[str] = []
	for key in ("finding", "diagnosis", "result", "classification", "label", "interpretation"):
		value = item.get(key)
		if value:
			parts.append(str(value))
			break
	for key in ("severity", "severity_level", "priority"):
		value = item.get(key)
		if value:
			parts.append(f"severity={value}")
			break
	for key in ("largest_diameter_mm", "tumor_volume_cm3", "ejection_fraction"):
		value = item.get(key)
		if value not in (None, ""):
			parts.append(f"{key}={value}")
	date_value = item.get("created_at") or item.get("date") or item.get("recorded_at")
	if date_value:
		parts.append(f"date={str(date_value)[:10]}")
	return "; ".join(parts) if parts else ""


def _format_patient_context_for_prompt(patient_context: dict[str, Any] | None) -> str:
	"""Compact plain-text summary (not JSON). Keeps prompt small and model-focused."""
	if not isinstance(patient_context, dict):
		return ""

	name = " ".join(
		str(p) for p in [patient_context.get("first_name"), patient_context.get("last_name")] if p
	).strip() or "Unknown"
	gender = patient_context.get("gender") or "unknown"
	dob = patient_context.get("date_of_birth") or "unknown"

	medical_history = patient_context.get("medical_history") or {}
	recent_cases = list(medical_history.get("recent_cases") or [])[:3]
	recent_ecg = list(medical_history.get("recent_ecg_results") or [])[:3]
	recent_mri = list(medical_history.get("recent_mri_results") or [])[:3]

	lines = [
		f"Patient: {name} | gender={gender} | dob={dob}",
	]
	if recent_mri:
		mri_lines = [s for s in (_summarize_finding(m) for m in recent_mri) if s]
		if mri_lines:
			lines.append("Recent MRI: " + " || ".join(mri_lines))
	if recent_ecg:
		ecg_lines = [s for s in (_summarize_finding(e) for e in recent_ecg) if s]
		if ecg_lines:
			lines.append("Recent ECG: " + " || ".join(ecg_lines))
	if recent_cases:
		case_lines = []
		for case in recent_cases:
			if not isinstance(case, dict):
				continue
			title = case.get("title") or case.get("chief_complaint") or case.get("diagnosis") or "case"
			status_value = case.get("status") or case.get("priority") or ""
			case_lines.append(f"{title} ({status_value})".strip())
		if case_lines:
			lines.append("Recent cases: " + "; ".join(case_lines))

	return "\n".join(lines)


def _augment_question_with_patient_context(question: str, patient_context: dict[str, Any] | None) -> str:
	context_blob = _format_patient_context_for_prompt(patient_context)
	if not context_blob:
		return question

	return (
		"Use the following patient clinical context when it is relevant. "
		"If a field is missing, say so instead of guessing.\n"
		f"PATIENT_CONTEXT:\n{context_blob}\n\n"
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
		return _enrich_conversation(conversation)

	profile_id = _resolve_profile_id(user)
	role = str(user.get("role") or "").strip().lower()
	if role == "patient" and conversation.get("patient_id") != profile_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
	if role != "patient" and conversation.get("doctor_id") != profile_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

	return _enrich_conversation(conversation)


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

	conversation_project_id = str(uuid.uuid4())
	conversation_metadata: dict[str, Any] = {
		"project_id": project_id,
		"conversation_project_id": conversation_project_id,
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

	# Surface conversation_project_id at the top level for easy access
	result = dict(conversation)
	result["conversation_project_id"] = (
		result.get("conversation_project_id")
		or (result.get("metadata") or {}).get("conversation_project_id")
		or conversation_project_id
	)
	return result

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
	conversation_project_id: str | None = Form(default=None),
	user: dict[str, Any] = CURRENT_USER_DEPENDENCY,
):
	if not project_id.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

	# Prefer the per-conversation UUID; fall back to the URL project_id only if
	# that one is a valid UUID itself. Raises a clear 400 otherwise.
	rag_project_id = _resolve_rag_project_id(
		url_project_id=project_id,
		conversation_project_id=conversation_project_id,
	)
	if not files:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

	role = str(user.get("role") or "").strip().lower()
	resolved_patient_id = str(patient_id or "").strip() if role != "patient" else _resolve_profile_id(user)
	if role != "patient" and not resolved_patient_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required")

	process_controller = ProcessController(project_id=rag_project_id)
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

		if vectordb_client is None or embedding_client is None or template_parser is None:
			missing = [n for n, v in [("vectordb", vectordb_client), ("embedding", embedding_client), ("template_parser", template_parser)] if v is None]
			rejected_files.append({"file": upload.filename or "unknown", "reason": f"Server NLP clients not ready: {', '.join(missing)}"})
			logger.error(f"Cannot index uploaded file — missing clients: {missing}")
			continue

		try:
			file_content = process_controller.get_file_content(file_id=relative_path)
			chunks = process_controller.process_file_content(file_content=file_content, file_id=relative_path)
			if not chunks:
				raise ValueError("No chunks generated")

			texts = [chunk.page_content for chunk in chunks]
			logger.info(f"Embedding {len(texts)} chunks for uploaded file: {filename}")
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
				generation_client=generation_client,  # not used during indexing
				embedding_client=embedding_client,
				template_parser=template_parser,
			)
			nlp_controller.index_into_vector_db(
				project_id=rag_project_id,
				texts=texts,
				vectors=vectors,
				metadata=metadata,
				do_reset=False,
			)
			logger.info(f"Indexed {len(chunks)} chunks for '{filename}' into collection '{rag_project_id}' under source_file_id='{upload_identifier}'")
			indexed_documents.append({"id": upload_identifier, "label": label})
		except Exception as exc:
			logger.error(f"Indexing failed for '{filename}': {exc}")
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

	# Each conversation gets its own isolated Qdrant collection via a unique
	# conversation_project_id. This prevents uploaded files from leaking across
	# conversations that share the same hospital_id.
	conversation_project_id = str(uuid.uuid4())

	conversation = await repo.create(
		{
			"title": str(payload.get("title") or "Medical Consultation").strip() or "Medical Consultation",
			"conversation_type": conversation_type,
			"patient_id": patient_id,
			"doctor_id": doctor_id,
			"hospital_id": hospital_id,
			"metadata": {
				"project_id": project_id,
				"conversation_project_id": conversation_project_id,
				"created_via": "nlp_routes",
			},
		}
	)
	if not conversation:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to create conversation")

	# Inject conversation_project_id at top level so the frontend can read it directly
	result = dict(conversation)
	result["conversation_project_id"] = (
		result.get("conversation_project_id")
		or (result.get("metadata") or {}).get("conversation_project_id")
		or conversation_project_id
	)
	return {"conversation": result}


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
	request_started = time.perf_counter()
	timings: dict[str, float] = {}
	phase_started = request_started

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

	# Use the per-conversation project_id for all vector operations so each
	# conversation has its own isolated Qdrant collection. Fall back to the
	# hospital-level project_id only if none was provided (legacy conversations).
	rag_project_id = _resolve_rag_project_id(
		url_project_id=project_id,
		conversation_project_id=search_request.conversation_project_id,
	)

	image_path = _resolve_uploaded_image_path(project_id=rag_project_id, image_ids=search_request.image_file_ids)

	nlp_controller = NLPController(
		vectorDB_client=vectordb_client,
		generation_client=generation_client,
		embedding_client=embedding_client,
		template_parser=template_parser,
	)
	timings["setup_s"] = time.perf_counter() - phase_started

	# Kick off the Supabase patient-context fetch in parallel with the rest of
	# the setup. The heavy work (embedding + vector search + LLM call) runs
	# after this, so overlapping the two I/O paths trims end-to-end latency.
	phase_started = time.perf_counter()
	patient_id_for_context = str(search_request.patient_id or "").strip()
	patient_context_task: asyncio.Task | None = None
	if patient_id_for_context:
		patient_context_task = asyncio.create_task(
			_build_patient_context(patient_id_for_context)
		)

	patient_context = None
	if patient_context_task is not None:
		try:
			patient_context = await patient_context_task
		except Exception as exc:
			logger.warning(f"Failed to fetch patient context for {patient_id_for_context}: {str(exc)}")
	timings["patient_context_s"] = time.perf_counter() - phase_started

	phase_started = time.perf_counter()
	question_for_model = _augment_question_with_patient_context(search_request.text, patient_context)
	timings["question_augmentation_s"] = time.perf_counter() - phase_started

	sources: list[dict[str, Any]] = []

	# Resolve timeout for local models (MedMO / PhiQA can be slow).
	settings = get_settings()
	local_timeout = 0
	if resolved_backend == "medmo":
		local_timeout = int(settings.MEDMO_REQUEST_TIMEOUT_SECONDS or 0)

	# Only filter by IDs that were actually indexed as chat attachments (chat_upload:: prefix).
	# ECG/MRI record UUIDs from context_file_ids are NOT indexed in the vector DB — they are
	# already embedded in the patient context above. Mixing them into filter_file_ids
	# causes Qdrant to find zero matching chunks and return no documents at all.
	#
	# When context_file_ids is empty we pass None so the search covers ALL
	# uploaded files in the conversation, not just the last one.
	indexed_file_ids = list({
		fid for fid in (
			list(search_request.context_file_ids or []) +
			list(search_request.image_file_ids or [])
		)
		if fid and str(fid).startswith(CHAT_UPLOAD_PREFIX)
	}) or None

	# Always retrieve enough chunks so that multiple uploaded files are
	# represented in the context. top_k=3 is too low when several documents
	# are indexed — bump to at least 8 so the model sees content from all files.
	effective_top_k = max(search_request.top_k, 8)

	try:
		phase_started = time.perf_counter()
		# All backends (including MedMO) go through the same RAG pipeline now.
		# This ensures uploaded documents are always retrieved and cited.
		rag_task = asyncio.to_thread(
			nlp_controller.answer_rag_question,
			project_id=rag_project_id,
			question=question_for_model,
			limit=effective_top_k,
			chat_history=search_request.chat_history,
			language=language,
			image_path=image_path,
			filter_file_ids=indexed_file_ids,
		)
		if local_timeout > 0:
			answer, full_prompt, chat_history_out, sources = await asyncio.wait_for(
				rag_task, timeout=local_timeout,
			)
		else:
			answer, full_prompt, chat_history_out, sources = await rag_task
		timings["answer_generation_s"] = time.perf_counter() - phase_started
	except asyncio.TimeoutError as exc:
		raise HTTPException(
			status_code=status.HTTP_504_GATEWAY_TIMEOUT,
			detail=f"Generation exceeded timeout ({local_timeout}s). Try a faster model.",
		) from exc
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to answer RAG question: {str(exc)}") from exc

	if not answer:
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
	
	phase_started = time.perf_counter()
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
		logger.error(f"Failed to persist user message for conversation {conversation_id}")

	# Store assistant response — keep metadata lean (no full_prompt to avoid DB bloat).
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
					"model_backend": resolved_backend,
					"model_id": resolved_model_id,
					"sources": sources,
				},
			),
		}
	)
	if assistant_message is None:
		logger.error(f"Failed to persist assistant message for conversation {conversation_id}")
	timings["persistence_s"] = time.perf_counter() - phase_started
	timings["total_s"] = time.perf_counter() - request_started
	logger.info(
		"RAG answer timings project_id=%s backend=%s timings=%s",
		project_id,
		resolved_backend,
		timings,
	)

	return {
		"conversation_id": conversation_id,
		"answer": answer,
		"sources": sources,
		"user_message": user_message,
		"assistant_message": assistant_message,
	}


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
