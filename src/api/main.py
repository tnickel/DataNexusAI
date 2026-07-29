import os
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse
from src.db.database import init_db
from src.api.routes import router

app = FastAPI(
    title="DataNexus AI – Data-Access Layer & Semantic Ontology Service",
    description="Abgesicherte REST-API Schicht mit Rollenbasierter Zugriffskontrolle (RBAC) und Ontologie-Registry für KI-Agenten.",
    version="0.2.0"
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "DataNexus AI Data-Access Layer", "version": "0.2.0"}

# Direct Documentation View Endpoints
@app.get("/docs/handbuch", response_class=PlainTextResponse)
@app.get("/api/v1/docs/handbuch", response_class=PlainTextResponse)
def get_betriebshandbuch():
    path = os.path.join("docs", "BETRIEBSHANDBUCH.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Betriebshandbuch nicht gefunden."

@app.get("/docs/fortschritt", response_class=PlainTextResponse)
@app.get("/api/v1/docs/fortschritt", response_class=PlainTextResponse)
def get_fortschrittsbericht():
    path = os.path.join("docs", "FORTSCHRITT.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Fortschrittsbericht nicht gefunden."

@app.get("/docs/pdf")
@app.get("/api/v1/docs/pdf")
def get_pdf_user_manual():
    pdf_path = os.path.join("docs", "BENUTZERHANDBUCH.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="DataNexus_AI_Benutzerhandbuch.pdf"
        )
    return PlainTextResponse("PDF Benutzerhandbuch nicht gefunden.", status_code=404)
