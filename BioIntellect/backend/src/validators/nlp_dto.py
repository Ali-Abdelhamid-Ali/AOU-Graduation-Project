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
    chunk_size: int = Field(
        default=100,
        gt=0,
        description="Chunk size for text splitting",
    )
    overlap_size: int = Field(
        default=20,
        ge=0,
        description="Chunk overlap size for text splitting",
    )
    do_reset: Optional[bool] = Field(
        False,
        description="Whether to reset the existing index before pushing new data",
    )

    @model_validator(mode="after")
    def validate_chunking(self):
        if self.overlap_size >= self.chunk_size:
            raise ValueError("overlap_size must be less than chunk_size")
        return self


class SearchRequest(BaseModel):
    text: str = Field(..., description="The search text string.")
    top_k: int = Field(default=3, gt=0, le=5)
    chat_history: list[dict[str, Any]] = Field(default_factory=list, max_length=100, description="Optional chat history for context")
    language: Optional[str] = Field(default="en", description="Response language: 'en' or 'ar'")