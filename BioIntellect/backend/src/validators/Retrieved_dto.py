from typing import Any, Optional

from pydantic import BaseModel, Field


class RetrievedItem(BaseModel):

    text: str = Field(
        ...,
        description="The text content of the retrieved item.",
    )

    score: float = Field(
        ...,
        description="The relevance score of the retrieved item.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Original chunk metadata (source_file_id, file_name, chunk_index, ...).",
    )

    source_file_id: Optional[str] = Field(
        default=None,
        description="Convenience accessor for the source document identifier.",
    )

    file_name: Optional[str] = Field(
        default=None,
        description="Human-readable source filename for citation display.",
    )
