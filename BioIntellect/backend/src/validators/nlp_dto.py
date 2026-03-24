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
    text: str = Field(
        ...,
        description="The search text string.",
    )
    top_k: int = Field(
        default=10,
        gt=0,
        description="The number of top results to return.",

    )
    limit: Optional[int] = Field(
        None,
        gt=0,
        description="Optional limit on the number of results to return. If not set, defaults to top_k."
    )   