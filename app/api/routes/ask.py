from fastapi import APIRouter, HTTPException

from app.llm.rag import ask_project
from app.schemas.ask import AskRequest, AskResponse


router = APIRouter(tags=["RAG"])


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    try:
        result = ask_project(request.question, request.project_name, request.top_k)
        return result

    except ValueError as exc:
        message = str(exc)

        if message.startswith("Project not found:"):
            raise HTTPException(status_code=404, detail=message) from exc

        raise HTTPException(status_code=400, detail=message) from exc