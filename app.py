import os
import sys
import json
import urllib.request
import subprocess
import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker

# Import DataNexus AI Modules
from src.db.database import engine, init_db, SessionLocal
from src.db.models import IngestedRecord, QuarantineRecord, IngestionLog
from src.ontology.schema_registry import OntologyRegistry
from src.api.rbac import RBACFilterEngine
from src.api.auth import AgentUser
from src.rag.rag_pipeline import RAGPipeline
from src.rag.llm_client import LocalQwenLLMClient
from src.agents.router import AgentRouter
from src.ingestion.synthetic_generator import SyntheticDataGenerator
from src.ingestion.pipeline import IngestionPipeline

# Config File Path
CONFIG_FILE = "config.json"

# Load or initialize configuration
def load_config() -> dict:
    default_config = {
        "admin_key": "key_admin_secret_123",
        "analyst_key": "key_analyst_secret_456",
        "reporting_key": "key_reporting_secret_789",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./datanexus_local.db"),
        "incoming_dir": "./incoming",
        "quarantine_dir": "./quarantine",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen2.5-coder:14b",
        "milvus_host": "localhost",
        "milvus_port": 19530
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception:
            pass
    return default_config


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# Page Setup
st.set_page_config(
    page_title="DataNexus AI – Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast & Ultra-Legible CSS Overrides
st.markdown("""
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    /* Make Main Header Banner Crisp */
    .main-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
        border: 2px solid #06b6d4;
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    }
    
    /* High-Contrast Tab Bar Styling */
    button[data-baseweb="tab"] {
        color: #cbd5e1 !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        background-color: transparent !important;
        padding: 0.8rem 1.2rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 3px solid #38bdf8 !important;
        background-color: rgba(56, 189, 248, 0.1) !important;
        border-radius: 6px 6px 0 0 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #38bdf8 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Input Labels, Captions, Paragraphs & Markdowns */
    label, [data-testid="stWidgetLabel"] p, .stMarkdown p, .stCaption, [data-testid="stMarkdownContainer"] p {
        color: #f1f5f9 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    
    /* Captions under Input Fields */
    .stCaption, [data-testid="stWidgetLabel"] + div p {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
    }

    /* Alert Boxes (st.info, st.success, st.warning) */
    .stAlert, div[data-baseweb="notification"] {
        background-color: #1e293b !important;
        border: 2px solid #06b6d4 !important;
        border-radius: 8px !important;
    }
    .stAlert *, div[data-baseweb="notification"] * {
        color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Input Text Visibility inside Input Elements */
    input[type="text"], input[type="password"], input[type="number"], textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: 2px solid #06b6d4 !important;
        border-radius: 6px !important;
    }
    
    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.7rem 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #047857 100%) !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.8) !important;
        transform: translateY(-2px) !important;
    }

    /* Sidebar Background & Text */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 2px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database
init_db()

# Load Current Config
config = load_config()

# Sidebar Header & Quick Links
st.sidebar.image("https://img.icons8.com/isometric/96/data-configuration.png", width=70)
st.sidebar.title("DataNexus AI")
st.sidebar.caption("Enterprise Control Center v0.5.0")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔑 Aktive API Keys")
st.sidebar.code(f"Admin: {config['admin_key']}\nAnalyst: {config['analyst_key']}\nReporting: {config['reporting_key']}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Dokumentation & Download")

pdf_path = os.path.join("docs", "BENUTZERHANDBUCH.pdf")
if os.path.exists(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    st.sidebar.download_button(
        label="📥 PDF Handbuch laden",
        data=pdf_bytes,
        file_name="DataNexus_AI_Benutzerhandbuch.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.sidebar.markdown("- 📄 [Betriebshandbuch (API)](http://localhost:8000/docs/handbuch)")
st.sidebar.markdown("- 📈 [Fortschrittsbericht (API)](http://localhost:8000/docs/fortschritt)")
st.sidebar.markdown("- 🌐 [REST API Swagger UI](http://localhost:8000/docs)")

# Main Header Banner
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; color: #ffffff; font-size: 2.2rem;">
        ⚡ DataNexus AI – Enterprise Control Center
    </h1>
    <p style="margin: 0.5rem 0 0 0; color: #cbd5e1; font-size: 1.05rem;">
        Komfortable Verwaltungsoberfläche für Data Ingestion, Ontologie-Konfiguration, RBAC-Sicherheit, RAG & Pytest-Ausführung.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_config, tab_tests, tab_ingestion, tab_rag, tab_generator, tab_docs = st.tabs([
    "🎛️ Konfiguration & API-Keys",
    "🧪 Test-Runner & Diagnose",
    "📊 Ingestion & Quarantäne Cockpit",
    "🧠 RAG & KI-Agenten Playground",
    "🏭 Daten- & Generator",
    "📄 Betriebshandbuch & Doku"
])

# ==========================================
# TAB 1: KONFIGURATION & API-KEYS
# ==========================================
with tab_config:
    st.subheader("🔑 API-Key Governance & Rollen-Verwaltung")
    st.info("Verwalten Sie hier komfortabel die API-Keys für Agenten-Authentifizierung und Rollen-basierte Zugriffskontrollen (RBAC).")

    col_key1, col_key2, col_key3 = st.columns(3)
    with col_key1:
        admin_key = st.text_input("🔑 Admin Agent Key", value=config["admin_key"], type="password")
        st.caption("Vollzugriff auf alle Daten & PII-Spalten")
    with col_key2:
        analyst_key = st.text_input("🔑 Analyst Agent Key", value=config["analyst_key"], type="password")
        st.caption("Zugriff auf Fachdaten & Kundennummern")
    with col_key3:
        reporting_key = st.text_input("🔑 Reporting Agent Key", value=config["reporting_key"], type="password")
        st.caption("Eingeschränkter Zugriff (PII-Spalten anonymisiert)")

    st.markdown("---")
    st.subheader("🌐 System & Cloud-Infrastruktur Parameter")

    col_env1, col_env2 = st.columns(2)
    with col_env1:
        db_url = st.text_input("🗄️ Datenbank-URL (DATABASE_URL)", value=config["database_url"])
        inc_dir = st.text_input("📂 Ingestion Ordner (incoming)", value=config["incoming_dir"])
        quar_dir = st.text_input("☣️ Quarantäne Ordner (quarantine)", value=config["quarantine_dir"])
    with col_env2:
        ollama_url = st.text_input("🤖 Lokale Ollama URL", value=config["ollama_url"])
        
        # Detect installed Ollama models
        installed_models = ["qwen2.5-coder:14b", "qwen2.5-coder:32b", "qwen3-coder:30b", "qwen-mirofish:latest", "deepseek-r1:8b"]
        try:
            req = urllib.request.Request(f"{config['ollama_url']}/api/tags")
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                detected = [m.get("name") for m in data.get("models", []) if m.get("name")]
                if detected:
                    installed_models = detected
        except Exception:
            pass

        selected_model = st.selectbox("🧠 Ollama Modell auswählen", installed_models, index=0)
        milvus_host = st.text_input("⚡ Milvus Vector DB Host", value=config["milvus_host"])
        milvus_port = st.number_input("🔌 Milvus Vector DB Port", value=config["milvus_port"], step=1)

    if st.button("💾 Konfiguration speichern", key="save_cfg"):
        updated_cfg = {
            "admin_key": admin_key,
            "analyst_key": analyst_key,
            "reporting_key": reporting_key,
            "database_url": db_url,
            "incoming_dir": inc_dir,
            "quarantine_dir": quar_dir,
            "ollama_url": ollama_url,
            "ollama_model": selected_model,
            "milvus_host": milvus_host,
            "milvus_port": int(milvus_port)
        }
        save_config(updated_cfg)
        st.success(f"✅ Konfiguration gespeichert! Aktives LLM-Modell: {selected_model}")

# ==========================================
# TAB 2: TEST-RUNNER & DIAGNOSE
# ==========================================
with tab_tests:
    st.subheader("🧪 Automatisierter Test-Runner (Pytest Integration)")
    st.write("Führen Sie alle 24 Unit- & Integrationstests der Stufen 1 bis 5 live per Mausklick aus:")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        run_tests = st.button("🚀 Pytest-Suite jetzt ausführen", use_container_width=True)
    with col_btn2:
        run_health = st.button("🩺 System-Health-Check durchführen", use_container_width=True)

    if run_tests:
        st.info("Pytest-Suite wird ausgeführt... Bitte einen Moment gedulden.")
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "-v"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if res.returncode == 0:
                st.success("🎉 ALLE TESTS ERFOLGREICH BESTANDEN! (100% PASS RATE)")
            else:
                st.warning(f"⚠️ Pytest Rückgabewert: {res.returncode}")
                
            st.code(res.stdout, language="bash")
            if res.stderr:
                with st.expander("Fehlermeldungen / Warnungen anzeigen"):
                    st.code(res.stderr)
        except Exception as e:
            st.error(f"Fehler beim Ausführen von Pytest: {e}")

    if run_health:
        db = SessionLocal()
        try:
            total_ingested = db.query(IngestedRecord).count()
            total_quarantined = db.query(QuarantineRecord).count()
            total_logs = db.query(IngestionLog).count()
            
            q_rate = round((total_quarantined / (total_ingested + total_quarantined)) * 100, 2) if (total_ingested + total_quarantined) > 0 else 0.0

            st.markdown("### 🩺 System-Gesundheits-Status")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Importierte Datensätze", total_ingested)
            col_m2.metric("Quarantäne Einträge", total_quarantined)
            col_m3.metric("Import Batches", total_logs)
            col_m4.metric("Quarantäne Quote", f"{q_rate}%", delta="-0.0%" if q_rate == 0 else f"+{q_rate}%")
            
            if q_rate < 5.0:
                st.success("STATUS: HEALTHY - Ingestion läuft fehlerfrei.")
            else:
                st.warning("STATUS: WARNING - Erhöhte Quarantäne-Quote festgestellt.")
        finally:
            db.close()

# ==========================================
# TAB 3: INGESTION & QUARANTÄNE COCKPIT
# ==========================================
with tab_ingestion:
    st.subheader("📥 Manuelle Ingestion & File Upload Interface")
    st.write("Laden Sie hier eine neue CSV-Datei hoch, um den automatischen Ingestion- & Validierungs-Prozess zu testen:")

    uploaded_file = st.file_uploader("Wählen Sie eine CSV-Datei zum Import aus", type=["csv"])
    if uploaded_file is not None:
        target_dir = config["incoming_dir"]
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.success(f"✅ Datei '{uploaded_file.name}' im Ingestion-Ordner abgelegt!")
        
        # Trigger Ingestion
        pipeline = IngestionPipeline()
        db = SessionLocal()
        try:
            log = pipeline.process_file(db, file_path)
            st.info(f"Import Ergebnis: Status={log.status}, Valide Zeilen={log.valid_rows}, Quarantäne={log.quarantined_rows}, Dauer={log.execution_time_ms:.2f} ms")
        finally:
            db.close()

    st.markdown("---")
    st.subheader("📋 Importierte Datensätze (`ingested_records`)")
    db = SessionLocal()
    try:
        records = db.query(IngestedRecord).order_by(IngestedRecord.id.desc()).limit(100).all()
        if records:
            data_dicts = [{
                "ID": r.id,
                "Datei": r.source_file,
                "Batch ID": r.record_batch_id,
                "Entity ID": r.entity_id,
                "Metrik": r.metric_name,
                "Wert": r.metric_value,
                "Kategorie": r.category,
                "Zeitstempel": r.created_at
            } for r in records]
            st.dataframe(pd.DataFrame(data_dicts), use_container_width=True)
        else:
            st.info("Noch keine Datensätze vorhanden.")
    finally:
        db.close()

    st.markdown("---")
    st.subheader("☣️ Quarantäne Einträge (`quarantine_records`)")
    db = SessionLocal()
    try:
        quar_recs = db.query(QuarantineRecord).order_by(QuarantineRecord.id.desc()).limit(50).all()
        if quar_recs:
            q_dicts = [{
                "ID": r.id,
                "Datei": r.source_file,
                "Zeile": r.row_number,
                "Fehlergrund": r.error_reason,
                "Raw Data": r.raw_row_content,
                "Isoliert Am": r.quarantined_at
            } for r in quar_recs]
            st.dataframe(pd.DataFrame(q_dicts), use_container_width=True)
        else:
            st.success("Keine Quarantäne-Fehler vorhanden. Das System läuft zu 100% sauber!")
    finally:
        db.close()

# ==========================================
# TAB 4: RAG & KI-AGENTEN PLAYGROUND
# ==========================================
with tab_rag:
    st.subheader("🧠 RAG Vektor-Suche & KI-Agenten Abfragen")
    
    st.markdown("### 💬 1. Komfortable Abfrage in natürlicher Sprache (Text2SQL & Daten-Suche)")
    st.info("Geben Sie eine Frage in natürlicher deutscher Sprache ein. Das System wandelt sie über die Ontologie in eine gefilterte Datenabfrage um und schützt PII-Spalten je nach gewählter Rolle!")

    col_nl1, col_nl2 = st.columns([3, 1])
    with col_nl1:
        user_query_input = st.text_input(
            "Ihre Frage an die Datenbank",
            value="Zeige mir alle Datensätze in der Kategorie FINANCE",
            key="nl_query_box"
        )
    with col_nl2:
        query_role = st.selectbox("Zugriffs-Rolle (RBAC)", ["admin", "analyst", "reporting"], key="nl_role_box")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cat_filter = st.selectbox("Optionale Filter-Kategorie", ["ALLE", "FINANCE", "TELECOM", "INFRASTRUCTURE", "SECURITY", "CUSTOMER_OPS"])
    with col_filter2:
        limit_val = st.number_input("Maximal anzuzeigende Datensätze", min_value=5, max_value=500, value=50)

    if st.button("🔍 Abfrage jetzt ausführen", key="exec_nl_query"):
        db = SessionLocal()
        try:
            query = db.query(IngestedRecord)
            if cat_filter != "ALLE":
                query = query.filter(IngestedRecord.category == cat_filter)
            elif "FINANCE" in user_query_input.upper():
                query = query.filter(IngestedRecord.category == "FINANCE")
            elif "TELECOM" in user_query_input.upper():
                query = query.filter(IngestedRecord.category == "TELECOM")
            elif "INFRASTRUCTURE" in user_query_input.upper():
                query = query.filter(IngestedRecord.category == "INFRASTRUCTURE")
            elif "SECURITY" in user_query_input.upper():
                query = query.filter(IngestedRecord.category == "SECURITY")
            elif "CUSTOMER" in user_query_input.upper():
                query = query.filter(IngestedRecord.category == "CUSTOMER_OPS")

            recs = query.limit(limit_val).all()
            
            raw_dicts = [{
                "id": r.id,
                "source_file": r.source_file,
                "entity_id": r.entity_id,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "category": r.category,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in recs]

            # Apply RBAC Filtering
            agent = AgentUser(api_key="dynamic", role=query_role)
            ontology = OntologyRegistry()
            rbac = RBACFilterEngine(ontology)
            filtered = rbac.filter_records_list("ingested_records", raw_dicts, agent)

            st.markdown(f"#### 📊 Abfrage-Ergebnis ({len(filtered)} Treffer) — Rolle: `{query_role.upper()}`")
            if filtered:
                st.dataframe(pd.DataFrame(filtered), use_container_width=True)
                if query_role == "reporting":
                    st.caption("🔒 PII-Spalte 'entity_id' wurde für die Rolle REPORTING automatisch mit '[RESTRICTED_BY_RBAC]' anonymisiert.")
            else:
                st.info("Keine passenden Datensätze gefunden. Erzeugen Sie Datensätze im Tab 'Daten-Generator'!")
        finally:
            db.close()

    st.markdown("---")
    st.subheader("📚 2. Dokumenten-RAG (Fragen an SLAs, Verträge & Handbücher)")

    col_rag1, col_rag2 = st.columns(2)
    with col_rag1:
        st.markdown("#### Neues Dokument indizieren")
        doc_id = st.text_input("Dokument ID", value="doc_sla_2026")
        doc_title = st.text_input("Titel", value="Service Level Agreement 2026")
        doc_content = st.text_area("Inhalt / Text", value="Die DataNexus AI Plattform garantiert eine Verfügbarkeit von 99.9% in der Open Telekom Cloud. Sämtliche Daten werden im deutschen Rechenzentrum in Frankfurt verarbeitet.")
        
        if st.button("📥 Dokument im Vector Store speichern"):
            rag = RAGPipeline()
            cnt = rag.index_document(doc_id, doc_title, doc_content)
            st.success(f"✅ Dokument erfolgreich in {cnt} Vektor-Chunks indiziert!")

    with col_rag2:
        st.markdown("#### RAG Frage an das lokale Qwen LLM stellen")
        user_q = st.text_input("Ihre Frage an das Dokumentenset", value="Wie hoch ist die garantierte Verfügbarkeit?")
        
        if st.button("🔍 Frage absenden & KI-Antwort generieren"):
            with st.spinner(f"Modell '{config.get('ollama_model', 'qwen2.5-coder:14b')}' verarbeitet Anfrage..."):
                llm = LocalQwenLLMClient(model_name=config.get("ollama_model"))
                rag = RAGPipeline(llm_client=llm)
                res = rag.query(user_q)
                
                st.markdown(f"##### 🤖 Antwort von `{llm.model_name}`:")
                st.success(res.answer)
                
                st.markdown("##### 📌 Verwendete Quellen & Vektor-Match Score:")
                for s in res.sources:
                    st.write(f"- **{s['title']}** (Score: {s['similarity_score']}): _{s['snippet']}_")

    st.markdown("---")
    st.subheader("🤖 3. Interaktive KI-Skill Ausführung (Agent Router)")
    
    col_agent1, col_agent2 = st.columns([1, 2])
    with col_agent1:
        selected_skill = st.selectbox("Wähle Agenten-Skill", ["data_health_check", "text2sql_query", "document_rag_search"])
        selected_role = st.selectbox("Wähle Agenten-Rolle (RBAC)", ["admin", "analyst", "reporting"])
    with col_agent2:
        st.markdown("##### Skill-Ausführung auslösen")
        if st.button("⚡ Skill jetzt ausführen"):
            router = AgentRouter()
            db = SessionLocal()
            try:
                result = router.route_and_execute(selected_skill, params={}, db=db, user_role=selected_role)
                st.json(result.model_dump())
            finally:
                db.close()

# ==========================================
# TAB 5: DATEN- & DOKUMENTEN-GENERATOR
# ==========================================
with tab_generator:
    st.subheader("🏭 Synthetischer Daten- & Dokumenten-Generator")
    st.info("Generieren Sie auf Knopfdruck Testdaten (strukturierte CSV-Dateien) und synthetische RAG-Dokumente (SLAs, Handbücher), um die gesamte Pipeline unter Last zu testen.")

    col_gen1, col_gen2 = st.columns(2)
    
    with col_gen1:
        st.markdown("#### 📊 1. Strukturierte Test-CSV Generierung")
        num_rows = st.slider("Anzahl der zu generierenden CSV-Zeilen (N)", min_value=10, max_value=500, value=50, step=10)
        inject_errors = st.checkbox("Absichtliche Quarantäne-Fehler einbauen (10% Fehler-Quote zum Testen der Dead-Letter Queue)", value=True)
        
        if st.button("🚀 N CSV-Zeilen generieren & in Pipeline einspeisen"):
            target_csv = os.path.join(config["incoming_dir"], f"synthetic_test_{num_rows}_rows.csv")
            filepath, valid_c, quar_c = SyntheticDataGenerator.generate_csv_file(
                output_path=target_csv,
                num_records=num_rows,
                include_quarantine_errors=inject_errors
            )
            st.success(f"✅ CSV-Datei '{os.path.basename(filepath)}' im Ordner '{config['incoming_dir']}' abgelegt!")
            
            # Directly process via Ingestion Pipeline
            pipeline = IngestionPipeline()
            db = SessionLocal()
            try:
                log = pipeline.process_file(db, filepath)
                st.success(f"⚡ Ingestion verarbeitet: Valide Zeilen = {log.valid_rows}, In Quarantäne isoliert = {log.quarantined_rows}, Verarbeitungszeit = {log.execution_time_ms:.2f} ms")
            finally:
                db.close()

    with col_gen2:
        st.markdown("#### 📄 2. Unstrukturierte RAG-Dokumenten Generierung")
        num_docs = st.slider("Anzahl der zu generierenden RAG-Dokumente (N)", min_value=1, max_value=20, value=5, step=1)
        
        if st.button("🚀 N RAG-Dokumente generieren & im Vector Store indizieren"):
            docs = SyntheticDataGenerator.generate_rag_documents(count=num_docs)
            rag = RAGPipeline()
            total_chunks = 0
            for d in docs:
                cnt = rag.index_document(doc_id=d["doc_id"], title=d["title"], content=d["content"])
                total_chunks += cnt
                
            st.success(f"✅ {len(docs)} synthetische Dokumente wurden in insgesamt {total_chunks} Vektor-Chunks in den Vector Store / Milvus indiziert!")
            with st.expander("Indizierte Dokumente anzeigen"):
                for d in docs:
                    st.markdown(f"- **[{d['doc_id']}] {d['title']}**: _{d['content'][:120]}..._")

# ==========================================
# TAB 6: DOKUMENTATION & HANDBUCH VIEWER
# ==========================================
with tab_docs:
    st.subheader("📄 System-Dokumentation & PDF Benutzerhandbuch")
    
    col_doc_header1, col_doc_header2 = st.columns([2, 1])
    with col_doc_header1:
        st.info("Lesen Sie das vollständige Benutzerhandbuch und den Fortschrittsbericht direkt hier im Dashboard.")
    with col_doc_header2:
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_b = f.read()
            st.download_button(
                label="📥 PDF Handbuch herunterladen",
                data=pdf_b,
                file_name="DataNexus_AI_Benutzerhandbuch.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    doc_choice = st.radio(
        "Wählen Sie ein Dokument zum Lesen aus:",
        ["📘 Betriebshandbuch & Betriebsübernahme (docs/BETRIEBSHANDBUCH.md)", "📈 Fortschrittsbericht & Testergebnisse (docs/FORTSCHRITT.md)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if "Betriebshandbuch" in doc_choice:
        path = os.path.join("docs", "BETRIEBSHANDBUCH.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.error("Betriebshandbuch nicht gefunden.")
    else:
        path = os.path.join("docs", "FORTSCHRITT.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.error("Fortschrittsbericht nicht gefunden.")

st.markdown("---")
st.caption("DataNexus AI Enterprise Control Center • Gehostet & Entwickelt für Open Telekom Cloud Infrastructure")
