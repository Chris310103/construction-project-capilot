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

class AskResponse(BaseModel):
    answer:str
    sources:list[SourceReference]