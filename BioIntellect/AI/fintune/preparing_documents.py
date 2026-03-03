from pathlib import Path
import json
from json import JSONDecoder
from typing import Any, Dict, List, Optional, Tuple
import time
from colorama import Fore, Style, init
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from litellm import completion, exceptions
import os

try:
    from .generated_prompt import chunking_prompt_template, qa_prompt_template
except ImportError:
    from generated_prompt import chunking_prompt_template, qa_prompt_template

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")
load_dotenv()
init(autoreset=True)

DEFAULT_OLLAMA_MODEL = "gpt-oss:120b-cloud"
DEFAULT_OLLAMA_API_BASE = "http://localhost:11434"


def _is_ollama_model_name(model_name: str) -> bool:
    if not isinstance(model_name, str):
        return False
    candidate = model_name.strip()
    if not candidate:
        return False
    return (
        candidate.startswith("ollama_chat/")
        or candidate.startswith("ollama/")
        or "/" not in candidate
    )


def _normalize_ollama_model_name(model_name: Optional[str]) -> str:
    if not isinstance(model_name, str):
        return ""

    candidate = model_name.strip()
    if not candidate:
        return ""
    if candidate.startswith("ollama_chat/"):
        return candidate
    if candidate.startswith("ollama/"):
        candidate = candidate.split("/", 1)[1].strip()
        return f"ollama_chat/{candidate}" if candidate else ""
    if "/" in candidate:
        return candidate
    return f"ollama_chat/{candidate}"
    
OLLAMA_MODEL = (os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL) or "").strip()
OLLAMA_API_BASE = (os.getenv("OLLAMA_API_BASE", DEFAULT_OLLAMA_API_BASE) or "").strip()
CHUNKING_MODEL_NAME = _normalize_ollama_model_name(
    os.getenv("CHUNKING_LITELLM_MODEL", OLLAMA_MODEL)
)
QA_MODEL_NAME = _normalize_ollama_model_name(os.getenv("QA_LITELLM_MODEL", OLLAMA_MODEL))
QA_FALLBACK_MODEL_NAME = _normalize_ollama_model_name(
    os.getenv("QA_FALLBACK_LITELLM_MODEL", "")
)
MAX_CONTEXT_CHARS = 8000
MAX_CHUNKING_INPUT_CHARS = int(os.getenv("MAX_CHUNKING_INPUT_CHARS", "50000"))
CHUNKING_MAX_TOKENS = int(os.getenv("CHUNKING_MAX_TOKENS", "16000"))
CHUNK_MIN_CHARS = 800
CHUNK_MAX_CHARS = 3500
SUPPORTED_EXTS = {".pdf", ".docx", ".pptx", ".html", ".htm", ".md", ".txt"}
OUTPUT_PATH = SCRIPT_DIR / "fine_tuning_data.json"
INSTRUCTION_OUTPUT_PATH = SCRIPT_DIR / "data" / "instruction.json"

# FIX #3: Centralise num_records so llm_call and max_tokens stay in sync
QA_NUM_RECORDS: int = int(os.getenv("QA_NUM_RECORDS", "12"))
QA_MAX_TOKENS_BASE: int = int(os.getenv("QA_MAX_TOKENS_BASE", "800"))
QA_MAX_TOKENS_PER_RECORD: int = int(os.getenv("QA_MAX_TOKENS_PER_RECORD", "320"))
QA_MAX_TOKENS_MIN: int = int(os.getenv("QA_MAX_TOKENS_MIN", "3000"))
QA_MAX_TOKENS_CAP: int = int(os.getenv("QA_MAX_TOKENS_CAP", "12000"))
QA_MAX_TOKENS: int = max(
    QA_MAX_TOKENS_MIN,
    min(
        max(QA_MAX_TOKENS_MIN, QA_MAX_TOKENS_CAP),
        QA_MAX_TOKENS_BASE + (max(1, QA_NUM_RECORDS) * QA_MAX_TOKENS_PER_RECORD),
    ),
)


def _get_ollama_api_base() -> Optional[str]:
    if not isinstance(OLLAMA_API_BASE, str):
        return None
    api_base = OLLAMA_API_BASE.strip()
    return api_base or None


def _classify_llm_error(exc: Exception) -> Tuple[str, str]:
    """Return (category, hint) for an LLM exception."""
    msg = str(exc)
    msg_lower = msg.lower()
    exc_name_lower = type(exc).__name__.lower()

    if isinstance(exc, exceptions.RateLimitError):
        return "rate limit", ""

    if "connection refused" in msg_lower or "failed to connect" in msg_lower:
        return (
            "ollama connection",
            " | Hint: start `ollama serve` and verify "
            f"OLLAMA_API_BASE={_get_ollama_api_base() or DEFAULT_OLLAMA_API_BASE}.",
        )

    if "timed out" in msg_lower or "timeout" in msg_lower:
        return (
            "ollama timeout",
            " | Hint: verify the Ollama server is reachable and the model is loaded; "
            "large local models may need longer to answer.",
        )

    if "notfounderror" in exc_name_lower or "404" in msg_lower or "not found" in msg_lower:
        return (
            "model not found",
            " | Hint: verify the configured model with `ollama list` and pull it if missing.",
        )

    if "jsondecodeerror" in exc_name_lower or (
        "json" in msg_lower and ("parse" in msg_lower or "decode" in msg_lower)
    ):
        return "JSON parse failure", ""

    return "other", ""


def _require_llm_runtime_config() -> Dict[str, Any]:
    global CHUNKING_MODEL_NAME, QA_MODEL_NAME, QA_FALLBACK_MODEL_NAME, OLLAMA_API_BASE

    OLLAMA_API_BASE = (_get_ollama_api_base() or "").strip()
    if not OLLAMA_API_BASE:
        raise SystemExit(
            "[FATAL] Missing OLLAMA_API_BASE. Set it before running the script."
        )

    CHUNKING_MODEL_NAME = _normalize_ollama_model_name(CHUNKING_MODEL_NAME)
    QA_MODEL_NAME = _normalize_ollama_model_name(QA_MODEL_NAME)
    QA_FALLBACK_MODEL_NAME = _normalize_ollama_model_name(QA_FALLBACK_MODEL_NAME)

    primary_models = {
        "CHUNKING_LITELLM_MODEL": CHUNKING_MODEL_NAME,
        "QA_LITELLM_MODEL": QA_MODEL_NAME,
    }
    for env_name, model_name in primary_models.items():
        if not model_name:
            raise SystemExit(f"[FATAL] Missing {env_name}. Set it to an Ollama model.")
        if not _is_ollama_model_name(model_name):
            raise SystemExit(
                f"[FATAL] {env_name} must point to an Ollama model. "
                f"Got: {model_name!r}"
            )

    fallback_enabled = bool(QA_FALLBACK_MODEL_NAME)
    if QA_FALLBACK_MODEL_NAME and not _is_ollama_model_name(QA_FALLBACK_MODEL_NAME):
        raise SystemExit(
            "[FATAL] QA_FALLBACK_LITELLM_MODEL must point to an Ollama model when set. "
            f"Got: {QA_FALLBACK_MODEL_NAME!r}"
        )

    return {
        "ollama_api_base": OLLAMA_API_BASE,
        "qa_fallback_enabled": fallback_enabled,
    }


def _llm_healthcheck(model_name: str, label: str) -> None:
    health_prompt = (
        'Return ONLY valid JSON object: {"ok": true}. '
        "No markdown. No extra text."
    )
    try:
        # FIX #4: healthcheck doesn't need to stream — pass stream_output=False
        # AND skip the expected_root so the dict {"ok":true} is accepted as-is.
        obj = _llm_json_call_with_rate_limit_fallback(
            prompt=health_prompt,
            max_tokens=64,
            expected_root=None,
            primary_model=model_name,
            fallback_model=QA_FALLBACK_MODEL_NAME,
            stream_output=False,
            call_label=f"{label}-healthcheck",
        )
    except Exception as exc:
        category, hint = _classify_llm_error(exc)
        raise SystemExit(
            f"[FATAL] LLM startup healthcheck failed [{category}] "
            f"(label={label}, model={model_name}): {type(exc).__name__}: {exc}{hint}"
        ) from exc

    if not isinstance(obj, dict) or obj.get("ok") is not True:
        raise SystemExit(
            "[FATAL] LLM startup healthcheck returned unexpected JSON. "
            f"Expected {{\"ok\": true}}, got: {obj!r}"
        )


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_first_json_value(raw_text: str, expected_root: Optional[str] = None) -> Any:
    text = (raw_text or "").replace("\ufeff", "").strip()
    if not text:
        raise ValueError("LLM returned an empty response.")

    candidates = [text]
    unfenced = _strip_code_fences(text)
    if unfenced != text:
        candidates.append(unfenced)

    decoder = JSONDecoder()
    starts_with_array_candidate = False

    for candidate in candidates:
        candidate_stripped = candidate.lstrip()
        if expected_root == "array" and candidate_stripped.startswith("["):
            starts_with_array_candidate = True

        try:
            parsed = json.loads(candidate)
            if expected_root == "array" and not isinstance(parsed, list):
                raise ValueError(
                    f"LLM returned valid JSON but root is {type(parsed).__name__}, expected array."
                )
            return parsed
        except json.JSONDecodeError:
            pass
        except ValueError:
            raise

        if expected_root == "array":
            continue

        for idx, char in enumerate(candidate):
            if char not in "[{":
                continue
            try:
                parsed, _ = decoder.raw_decode(candidate[idx:])
                return parsed
            except json.JSONDecodeError:
                continue

    if expected_root == "array" and starts_with_array_candidate:
        raise ValueError(
            "Could not parse a complete JSON array from LLM response "
            "(likely truncated by max_tokens). Increase the max_tokens for this call "
            "(CHUNKING_MAX_TOKENS for chunking or QA max-token settings for QA), "
            "or reduce prompt size."
        )

    snippet = text[:300].replace("\n", " ")
    raise ValueError(f"Could not parse JSON from LLM response: {snippet!r}")


def _normalize_records(obj: Any) -> List[Dict[str, str]]:
    if isinstance(obj, list):
        raw_records = obj
    elif isinstance(obj, dict):
        if isinstance(obj.get("generated"), list):
            raw_records = obj["generated"]
        elif isinstance(obj.get("questions_and_answers"), list):
            raw_records = obj["questions_and_answers"]
        elif "question" in obj and "answer" in obj:
            raw_records = [obj]
        else:
            raise ValueError(
                f"Unexpected LLM JSON object keys: {sorted(obj.keys())}. "
                "Expected list, 'generated', or 'questions_and_answers'."
            )
    else:
        raise ValueError(f"Unexpected LLM JSON type: {type(obj)}")

    normalized: List[Dict[str, str]] = []
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            continue
        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            continue
        normalized.append({"question": question, "answer": answer})

    if not normalized:
        raise ValueError("No valid {question, answer} records were found.")

    return normalized


def _normalize_chunks(obj: Any) -> List[Dict[str, str]]:
    if not isinstance(obj, list):
        raise ValueError(f"Chunking response must be a JSON array, got {type(obj)}")

    normalized: List[Dict[str, str]] = []
    for item in obj:
        if not isinstance(item, dict):
            continue

        chunk_id = item.get("chunk_id")
        chunk_title = item.get("chunk_title", "")
        chunk_text = item.get("chunk_text")

        if not isinstance(chunk_id, str) or not isinstance(chunk_text, str):
            continue
        if not isinstance(chunk_title, str):
            chunk_title = str(chunk_title or "")

        chunk_id = chunk_id.strip()
        chunk_title = chunk_title.strip()
        chunk_text = chunk_text.strip()
        if not chunk_id or not chunk_text:
            continue

        normalized.append(
            {
                "chunk_id": chunk_id,
                "chunk_title": chunk_title,
                "chunk_text": chunk_text,
            }
        )

    if not normalized:
        raise ValueError("No valid {chunk_id, chunk_title, chunk_text} chunks were found.")

    return normalized


def _truncate_context(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False

    cutoff = text.rfind(" ", 0, max_chars)
    if cutoff < int(max_chars * 0.7):
        cutoff = max_chars
    return text[:cutoff].rstrip(), True


def _qa_max_tokens_for_records(num_records: int) -> int:
    estimated = QA_MAX_TOKENS_BASE + (max(1, num_records) * QA_MAX_TOKENS_PER_RECORD)
    capped = min(max(QA_MAX_TOKENS_MIN, QA_MAX_TOKENS_CAP), estimated)
    return max(QA_MAX_TOKENS_MIN, capped)


def _split_text_for_chunking(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    segments: List[str] = []
    cursor = 0
    n = len(text)
    min_cut = int(max_chars * 0.6)

    while cursor < n:
        remaining = n - cursor
        if remaining <= max_chars:
            seg = text[cursor:].strip()
            if seg:
                segments.append(seg)
            break

        end = min(cursor + max_chars, n)
        window = text[cursor:end]

        cut = window.rfind("\n\n")
        if cut < min_cut:
            cut = window.rfind("\n")
        if cut < min_cut:
            cut = window.rfind(" ")
        if cut < min_cut:
            cut = len(window)  # hard cut — no good boundary found

        seg = window[:cut].strip()
        if seg:
            segments.append(seg)

        # FIX #8: guarantee forward progress even when cut == 0
        advance = cut if cut > 0 else max_chars
        cursor += advance

    return segments or [text]


def _renumber_chunks(chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "chunk_id": f"c{idx:04d}",
            "chunk_title": chunk.get("chunk_title", ""),
            "chunk_text": chunk.get("chunk_text", ""),
        }
        for idx, chunk in enumerate(chunks, start=1)
    ]


def _document_to_text(doc: Any) -> str:
    for method_name in ("export_to_markdown", "export_to_text", "to_markdown", "to_text"):
        method = getattr(doc, method_name, None)
        if callable(method):
            try:
                value = method()
            except TypeError:
                continue
            if isinstance(value, str) and value.strip():
                return value

    for attr_name in ("text", "markdown", "content"):
        value = getattr(doc, attr_name, None)
        if isinstance(value, str) and value.strip():
            return value

    dumped = str(doc)
    if dumped and dumped.strip():
        return dumped

    raise ValueError("Could not extract text from converted document.")


def _get_field(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key, default)
    try:
        return obj[key]  # type: ignore[index]
    except Exception:
        return default


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
        return _content_to_text(content.get("content"))
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            t = _content_to_text(item)
            if t:
                parts.append(t)
        return "".join(parts)
    text_attr = getattr(content, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    content_attr = getattr(content, "content", None)
    if content_attr is not None:
        return _content_to_text(content_attr)
    return ""


def _extract_stream_text(event: Any) -> str:
    choices = _get_field(event, "choices", [])
    if not choices:
        return ""
    choice = choices[0]
    delta = _get_field(choice, "delta")
    if delta is not None:
        return _content_to_text(_get_field(delta, "content")) or _content_to_text(
            _get_field(delta, "text")
        )
    message = _get_field(choice, "message")
    if message is not None:
        return _content_to_text(_get_field(message, "content"))
    return ""


def _extract_non_stream_text(response: Any) -> str:
    choices = _get_field(response, "choices", [])
    if not choices:
        return ""
    choice = choices[0]
    message = _get_field(choice, "message")
    if message is not None:
        return _content_to_text(_get_field(message, "content"))
    delta = _get_field(choice, "delta")
    if delta is not None:
        return _content_to_text(_get_field(delta, "content"))
    return ""


def _llm_json_call(
    prompt: str,
    max_tokens: int = 2000,
    system_prompt: Optional[str] = None,
    expected_root: Optional[str] = None,
    model_name: Optional[str] = None,
    stream_output: bool = True,
) -> Any:
    selected_model = _normalize_ollama_model_name(model_name or QA_MODEL_NAME)
    if not selected_model:
        raise ValueError("No model name configured for _llm_json_call.")
    if not _is_ollama_model_name(selected_model):
        raise ValueError(
            f"Only Ollama models are supported by this script. Got: {selected_model!r}"
        )

    ollama_api_base = _get_ollama_api_base()
    if not ollama_api_base:
        raise ValueError("OLLAMA_API_BASE is not configured.")

    messages = [{"role": "user", "content": prompt}]
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}, *messages]

    request_payload: Dict[str, Any] = dict(
        model=selected_model,
        messages=messages,
        max_tokens=max_tokens,
        api_base=ollama_api_base,
    )

    stream = completion(**request_payload, stream=True)

    collected = ""
    for event in stream:
        delta_text = _extract_stream_text(event)
        if delta_text:
            if stream_output:
                print(Fore.LIGHTBLUE_EX + delta_text + Fore.RESET, end="")
            collected += delta_text

    if not collected.strip():
        print(
            Fore.YELLOW
            + "[INFO] Empty stream response; retrying with stream=False."
            + Style.RESET_ALL
        )
        response = completion(**request_payload, stream=False)
        collected = _extract_non_stream_text(response)
        if collected and stream_output:
            print(Fore.LIGHTBLUE_EX + collected + Fore.RESET, end="")

    return _extract_first_json_value(collected, expected_root=expected_root)


def _can_use_model(model_name: Optional[str]) -> bool:
    normalized_model = _normalize_ollama_model_name(model_name)
    return bool(normalized_model) and bool(_get_ollama_api_base()) and _is_ollama_model_name(
        normalized_model
    )


def _llm_json_call_with_rate_limit_fallback(
    *,
    prompt: str,
    max_tokens: int,
    expected_root: Optional[str],
    primary_model: str,
    fallback_model: Optional[str],
    stream_output: bool,
    call_label: str,
    system_prompt: Optional[str] = None,
) -> Any:
    normalized_primary_model = _normalize_ollama_model_name(primary_model)
    normalized_fallback_model = _normalize_ollama_model_name(fallback_model)

    try:
        return _llm_json_call(
            prompt,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            expected_root=expected_root,
            model_name=normalized_primary_model,
            stream_output=stream_output,
        )
    except exceptions.RateLimitError:
        if (
            not normalized_fallback_model
            or normalized_fallback_model == normalized_primary_model
            or not _can_use_model(normalized_fallback_model)
        ):
            raise

        print(
            Fore.YELLOW
            + f"[WARN] Rate limit on {call_label} model {normalized_primary_model}; "
              f"retrying once with fallback {normalized_fallback_model}."
            + Style.RESET_ALL
        )
        return _llm_json_call(
            prompt,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            expected_root=expected_root,
            model_name=normalized_fallback_model,
            stream_output=stream_output,
        )


def _llm_chunk_call_single(chunking_input: str) -> List[Dict[str, str]]:
    prompt = chunking_prompt_template(
        chunking_input,
        min_chars=CHUNK_MIN_CHARS,
        max_chars=CHUNK_MAX_CHARS,
    )
    obj = _llm_json_call_with_rate_limit_fallback(
        prompt=prompt,
        max_tokens=CHUNKING_MAX_TOKENS,
        expected_root="array",
        primary_model=CHUNKING_MODEL_NAME,
        fallback_model=QA_FALLBACK_MODEL_NAME,
        stream_output=False,
        call_label="chunking",
    )
    return _normalize_chunks(obj)


def llm_chunk_call(raw_text: str) -> List[Dict[str, str]]:
    initial_segments = _split_text_for_chunking(raw_text, MAX_CHUNKING_INPUT_CHARS)
    if len(initial_segments) > 1:
        print(
            Fore.CYAN
            + f"[chunking] splitting document into {len(initial_segments)} chunking passes "
              f"(max {MAX_CHUNKING_INPUT_CHARS} chars/pass)."
            + Style.RESET_ALL
        )

    all_chunks: List[Dict[str, str]] = []
    pending: List[Tuple[str, int, str]] = [
        (seg, 0, f"{i + 1}/{len(initial_segments)}")
        for i, seg in reversed(list(enumerate(initial_segments)))
    ]

    while pending:
        segment_text, depth, label = pending.pop()
        print(
            Fore.CYAN
            + f"[chunking] pass {label} | chars={len(segment_text)} | split_depth={depth}"
            + Style.RESET_ALL
        )

        try:
            seg_chunks = _llm_chunk_call_single(segment_text)
            all_chunks.extend(seg_chunks)
            continue
        except Exception as exc:
            category, _ = _classify_llm_error(exc)
            msg = str(exc).lower()
            can_retry_smaller = len(segment_text) > 8000 and (
                category == "JSON parse failure"
                or "truncated by max_tokens" in msg
                or "complete json array" in msg
                or "unterminated" in msg
            )
            if not can_retry_smaller:
                raise

            mid_target = max(4000, len(segment_text) // 2)
            smaller_segments = _split_text_for_chunking(segment_text, mid_target)
            if len(smaller_segments) <= 1:
                raise

            print(
                Fore.YELLOW
                + f"[chunking] pass {label} likely produced truncated JSON; "
                  f"retrying as {len(smaller_segments)} smaller passes."
                + Style.RESET_ALL
            )
            for sub_idx, sub_seg in reversed(list(enumerate(smaller_segments, start=1))):
                pending.append((sub_seg, depth + 1, f"{label}.{sub_idx}"))

    return _renumber_chunks(all_chunks)


def llm_call(data: str, num_records: int = QA_NUM_RECORDS) -> List[dict]:
    """Generate Q/A pairs for a single chunk."""
    # FIX #1: pass expected_root="array" so a wrong root type raises immediately.
    # FIX #2: scale max_tokens to num_records with a safer estimate for evidence-rich answers.
    max_tokens = _qa_max_tokens_for_records(num_records)
    obj = _llm_json_call_with_rate_limit_fallback(
        prompt=qa_prompt_template(data, num_records),
        max_tokens=max_tokens,
        expected_root="array",       # ← FIX #1
        primary_model=QA_MODEL_NAME,
        fallback_model=QA_FALLBACK_MODEL_NAME,
        stream_output=True,
        call_label="qa",
    )
    return _normalize_records(obj)


if __name__ == "__main__":
    folder = Path(
        r"D:\AMIT\AOU PROJECT\AOU Graduation Project\AOU-Graduation-Project\BioIntellect\AI\fintune\fine-tuning data\l1"
    )

    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"[FATAL] Input folder not found or is not a directory: {folder}")

    input_files = sorted(
        [fp for fp in folder.rglob("*") if fp.is_file() and fp.suffix.lower() in SUPPORTED_EXTS],
        key=lambda p: str(p).lower(),
    )
    if not input_files:
        raise SystemExit(
            "[FATAL] No supported files found in input folder: "
            f"{folder} | Supported extensions: {sorted(SUPPORTED_EXTS)}"
        )

    runtime_cfg = _require_llm_runtime_config()
    print(
        Fore.CYAN
        + f"[startup] ollama_api_base={runtime_cfg['ollama_api_base']} | "
          f"chunking_model={CHUNKING_MODEL_NAME} | "
          f"qa_model={QA_MODEL_NAME} | "
          f"qa_fallback_model={QA_FALLBACK_MODEL_NAME or '(disabled)'} | "
          f"qa_fallback_enabled={'yes' if runtime_cfg['qa_fallback_enabled'] else 'no'} | "
          f"qa_num_records={QA_NUM_RECORDS} | qa_max_tokens={QA_MAX_TOKENS} | "
          f"folder={folder}"
        + Style.RESET_ALL
    )
    _llm_healthcheck(CHUNKING_MODEL_NAME, "chunking")
    if QA_MODEL_NAME != CHUNKING_MODEL_NAME:
        _llm_healthcheck(QA_MODEL_NAME, "qa")
    print(Fore.CYAN + "[startup] LLM healthcheck passed (chunking/qa)." + Style.RESET_ALL)

    converter = DocumentConverter()

    dataset: List[dict] = []
    instructions: List[dict] = []

    total_chunks = 0
    skipped_chunks = 0
    valid_records = 0

    MAX_RETRIES_PER_CHUNK = 10
    BASE_SLEEP_SECONDS = 30

    for fp in input_files:
        try:
            result = converter.convert(str(fp))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(
                Fore.RED
                + f"[WARN] Skipping {fp.name}: conversion failed ({type(exc).__name__}: {exc})"
                + Style.RESET_ALL
            )
            continue

        doc = getattr(result, "document", result)
        try:
            doc_text = _document_to_text(doc)
        except Exception as exc:
            print(
                Fore.RED
                + f"[WARN] Skipping {fp.name}: failed to extract document text "
                  f"({type(exc).__name__}: {exc})"
                + Style.RESET_ALL
            )
            continue

        try:
            chunks = llm_chunk_call(doc_text)
        except Exception as exc:
            category, hint = _classify_llm_error(exc)
            print(
                Fore.RED
                + f"[WARN] Skipping {fp.name}: chunking failed [{category}] "
                  f"({type(exc).__name__}: {exc}){hint}"
                + Style.RESET_ALL
            )
            continue

        for i, chunk in enumerate(chunks):
            total_chunks += 1

            chunk_title = chunk.get("chunk_title", "")
            raw_text = chunk.get("chunk_text", "")
            if not isinstance(chunk_title, str):
                chunk_title = str(chunk_title or "")
            if not isinstance(raw_text, str):
                raw_text = str(raw_text or "")
            chunk_title = chunk_title.strip()
            raw_text = raw_text.strip()

            if not raw_text:
                skipped_chunks += 1
                print(
                    Fore.YELLOW
                    + f"[WARN] Skipping [{fp.name}][{i}] empty LLM chunk."
                    + Style.RESET_ALL
                )
                continue

            print(
                Fore.YELLOW
                + f"[{fp.name}][{i}] chunk {chunk.get('chunk_id', '')} raw text:\n{raw_text[:300]}..."
                + Style.RESET_ALL
            )

            # Avoid duplicating the title if the chunk text already begins with it.
            if chunk_title and raw_text.startswith(chunk_title):
                enriched_text = raw_text
            else:
                enriched_text = f"{chunk_title}\n{raw_text}".strip() if chunk_title else raw_text

            print(
                Fore.GREEN
                + f"[{fp.name}][{i}] enriched text:\n{enriched_text[:300]}..."
                + Style.RESET_ALL
            )

            llm_input, is_truncated = _truncate_context(enriched_text)
            if is_truncated:
                print(
                    Fore.CYAN
                    + f"[{fp.name}][{i}] context truncated: "
                      f"{len(enriched_text)} -> {len(llm_input)} chars."
                    + Style.RESET_ALL
                )

            attempt = 0
            success = False
            records: List[dict] = []
            skip_counted_for_chunk = False

            while attempt < MAX_RETRIES_PER_CHUNK:
                attempt += 1
                try:
                    records = llm_call(llm_input)
                    success = True
                    break
                except exceptions.RateLimitError:
                    wait_time = BASE_SLEEP_SECONDS * attempt
                    print(
                        Fore.YELLOW
                        + f"[WARN] Rate limit for [{fp.name}][{i}] "
                          f"(attempt {attempt}/{MAX_RETRIES_PER_CHUNK}). "
                          f"Waiting {wait_time}s then retrying..."
                        + Style.RESET_ALL
                    )
                    time.sleep(wait_time)
                except Exception as exc:
                    skipped_chunks += 1
                    skip_counted_for_chunk = True
                    category, hint = _classify_llm_error(exc)
                    print(
                        Fore.RED
                        + f"[WARN] Skipping [{fp.name}][{i}] due to LLM failure "
                          f"[{category}]: {type(exc).__name__}: {exc}{hint}"
                        + Style.RESET_ALL
                    )
                    break

            if not success:
                if attempt >= MAX_RETRIES_PER_CHUNK and not skip_counted_for_chunk:
                    skipped_chunks += 1
                    print(
                        Fore.RED
                        + f"[WARN] Skipping [{fp.name}][{i}] after "
                          f"{MAX_RETRIES_PER_CHUNK} failed attempts (RateLimit / errors)."
                        + Style.RESET_ALL
                    )
                continue

            valid_records += len(records)
            dataset.extend(records)

            for pair in records:
                question = pair.get("question", "").strip()
                answer = pair.get("answer", "").strip()
                if not question or not answer:
                    continue
                instructions.append(
                    {
                        "input": (
                            f"Context:\n{llm_input}\n\n"
                            f"Task: Answer the following question based only on the context.\n"
                            f"Question: {question}"
                        ),
                        "output": answer,
                    }
                )

            print(
                Fore.LIGHTGREEN_EX
                + f"[{fp.name}][{i}] accepted records: {len(records)}"
                + Style.RESET_ALL
            )

            # FIX #6: configurable inter-chunk sleep via env var
            inter_chunk_sleep = float(os.getenv("INTER_CHUNK_SLEEP", "1"))
            time.sleep(inter_chunk_sleep)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    instruction_path = INSTRUCTION_OUTPUT_PATH
    instruction_path.parent.mkdir(parents=True, exist_ok=True)
    with open(instruction_path, "w", encoding="utf-8") as f:
        json.dump(instructions, f, ensure_ascii=False, indent=2)

    print(
        Fore.MAGENTA
        + "\nRun summary:\n"
        + f"- total chunks:    {total_chunks}\n"
        + f"- skipped chunks:  {skipped_chunks}\n"
        + f"- valid records:   {valid_records}\n"
        + f"- raw QA output:   {OUTPUT_PATH.resolve()}\n"
        + f"- fine-tune data:  {instruction_path.resolve()}"
        + Style.RESET_ALL
    )
