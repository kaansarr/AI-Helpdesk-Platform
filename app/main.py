from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.daily_report import router as daily_report_router
from app.api.chat import router as chat_router
from app.api.rag import router as rag_router
from app.api.documents import router as documents_router
from app.api.knowledge_gaps import router as knowledge_gaps_router

app = FastAPI(
    title="AI Helpdesk Platform",
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# MCP Agent endpoint'leri
app.include_router(chat_router)


# RAG endpoint'leri
app.include_router(rag_router)

app.include_router(documents_router)

app.include_router(knowledge_gaps_router)
app.include_router(daily_report_router)
@app.get("/health")
def health():
    return {"status": "ok"}