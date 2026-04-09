from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class PushRequest(BaseModel):
    file_id: Optional[str] = Field(
        default=None,
        description="Uploaded file identifier",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata that may include file_id",
    )
    chunk_size: Optional[int] = Field(
        default=None,
        gt=0,
        le=4000,
        description="Chunk size. Leave null to auto-pick based on file size.",
    )
    overlap_size: Optional[int] = Field(
        default=None,
        ge=0,
        description="Chunk overlap. Leave null to auto-pick based on file size.",
    )
    do_reset: Optional[bool] = Field(
        False,
        description="Whether to reset the existing index before pushing new data",
    )

    @model_validator(mode="after")
    def validate_chunking(self):
        if (
            self.chunk_size is not None
            and self.overlap_size is not None
            and self.overlap_size >= self.chunk_size
        ):
            raise ValueError("overlap_size must be less than chunk_size")
        return self


class SearchRequest(BaseModel):
    text: str = Field(..., description="The search text string.")
    top_k: int = Field(default=3, gt=0, le=5)
    chat_history: list[dict[str, Any]] = Field(default_factory=list, max_length=100, description="Optional chat history for context")
    language: Optional[str] = Field(default="en", description="Response language: 'en' or 'ar'")
    model_backend: Optional[str] = Field(
        default=None,
        description="Optional generation backend override. Supported: cohere, openai, medmo, phi_qa",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation identifier for persisted chat history",
    )
    patient_id: Optional[str] = Field(
        default=None,
        description="Patient profile ID, required when a non-patient starts a new conversation",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional conversation title for newly created persisted conversations",
    )
    context_file_ids: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Optional document file IDs to bind to the message context",
    )
    image_file_ids: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Optional image file IDs to bind to the message context",
    )
    conversation_project_id: Optional[str] = Field(
        default=None,
        description="Per-conversation isolated project_id for scoped vector storage",
    )