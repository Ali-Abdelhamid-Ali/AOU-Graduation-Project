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
