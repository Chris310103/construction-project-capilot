from pydantic import BaseModel, ConfigDict, Field

class AskRequest(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)

    question:str=Field(min_length=1)
    project_name:str=Field(default="Demo Boston Office Tower", min_length=1)
    top_k:int=Field(default=3, ge=1, le=20)

class SourceReference(BaseModel):
    id:str
    file_name:str
    location:str
    chunk_id:int

class DataSourceReference(BaseModel):
    tool: str
    tables: list[str]
    project_name: str
    filters: dict[str, str | bool] = Field(default_factory=dict)
    as_of_date: str | None = None
    contains_unverified_links: bool | None = None

class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    data_sources: list[DataSourceReference] = Field(default_factory=list)

