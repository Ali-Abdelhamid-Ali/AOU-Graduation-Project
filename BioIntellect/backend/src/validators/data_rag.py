from pydantic import BaseModel, Field, field_validator
from typing import Optional


class processRecquest(BaseModel):
    file_id: str = Field(..., description="the id of the file to be processed")
    chunk_size: Optional[int] = Field(None, description="Chunk size. Leave null to auto-pick based on file size.")
    overlap_size: Optional[int] = Field(None, description="Chunk overlap. Leave null to auto-pick based on file size.")
    do_reset: Optional[bool] = Field(False, description="whether to reset the processing state for the file")

    @field_validator("file_id")
    @classmethod
    def validate_file_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("file_id is required")
        if "/" in value or "\\" in value or ".." in value:
            raise ValueError("file_id contains invalid path characters")
        return value

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("chunk_size must be greater than 0")
        return value

    @field_validator("overlap_size")
    @classmethod
    def validate_overlap_size(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("overlap_size must be greater than or equal to 0")
        return value