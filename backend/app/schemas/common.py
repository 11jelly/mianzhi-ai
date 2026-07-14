from pydantic import BaseModel, Field


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class PageResponse[T](BaseModel):
    items: list[T]
    meta: PageMeta
