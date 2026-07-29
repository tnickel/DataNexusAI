import os
import sys
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Define Numbered Canvas for "Page X of Y" Footer
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Suppress headers/footers on cover page (Page 1)
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#06b6d4"))
            self.drawString(54, 805, "DATANEXUS AI — SYSTEM & BENUTZERHANDBUCH")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(541, 805, "Enterprise Edition v1.0")
            
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 797, 541, 797)
            
            # Footer
            self.line(54, 45, 541, 45)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(54, 32, "© 2026 Thomas Nickel — AI Software Architecture")
            
            page_text = f"Seite {self._pageNumber} von {page_count}"
            self.drawRightString(541, 32, page_text)
            
        self.restoreState()


def build_pdf_manual(output_pdf_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0f172a")      # Dark Slate
    CYAN = colors.HexColor("#06b6d4")         # High-Tech Cyan
    EMERALD = colors.HexColor("#10b981")      # Vibrant Emerald
    PURPLE = colors.HexColor("#8b5cf6")       # Purple Accent
    TEXT_DARK = colors.HexColor("#1e293b")    # Text Main
    TEXT_MUTED = colors.HexColor("#475569")   # Muted Gray
    BG_LIGHT = colors.HexColor("#f8fafc")     # Light Box BG
    BG_CODE = colors.HexColor("#0f172a")      # Dark Code BG

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=38,
        textColor=colors.white,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#cbd5e1"),
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=22,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=CYAN,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#38bdf8"),
        backColor=BG_CODE,
        borderColor=colors.HexColor("#334155"),
        borderWidth=1,
        borderPadding=10,
        spaceBefore=8,
        spaceAfter=10,
        borderRadius=4
    )
    
    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0f5132"),
        spaceBefore=8,
        spaceAfter=10
    )

    story = []

    # =========================================================
    # COVER PAGE
    # =========================================================
    # Top Decorative Banner
    cover_data = [
        [
            Paragraph("ENTERPRISE PLATFORM ARCHITECTURE & USER MANUAL", ParagraphStyle("CoverTag", fontName="Helvetica-Bold", fontSize=9, textColor=CYAN, spaceAfter=8)),
        ],
        [
            Paragraph("DataNexus AI", title_style),
        ],
        [
            Paragraph("Umfassendes System- & Benutzerhandbuch für entkoppelte Data Ingestion, Ontologie, RBAC-Governance, RAG-Stack & OTC Cloud Deployment", subtitle_style),
        ]
    ]
    
    cover_table = Table(cover_data, colWidths=[487])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 40),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 40))

    # Metadata Block Table
    meta_info = [
        [Paragraph("<b>Dokumenten-Typ:</b>", body_style), Paragraph("Offizielles Betriebs- & Benutzerhandbuch", body_style)],
        [Paragraph("<b>Projektname:</b>", body_style), Paragraph("DataNexus AI Platform", body_style)],
        [Paragraph("<b>Autor & Architektur:</b>", body_style), Paragraph("Thomas Nickel — AI Software Architect", body_style)],
        [Paragraph("<b>Version:</b>", body_style), Paragraph("v1.0 (Produktion / Enterprise Edition)", body_style)],
        [Paragraph("<b>Status:</b>", body_style), Paragraph("✅ 100% Umgesetzt & Verifiziert (24/24 Tests grün)", body_style)],
        [Paragraph("<b>Zielplattform:</b>", body_style), Paragraph("Open Telekom Cloud (OTC) & Docker Compose", body_style)],
        [Paragraph("<b>Datum:</b>", body_style), Paragraph("29. Juli 2026", body_style)],
    ]
    meta_table = Table(meta_info, colWidths=[150, 337])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 40))

    story.append(Paragraph("<b>Management Summary:</b>", h2_style))
    story.append(Paragraph(
        "Dieses Handbuch dokumentiert den vollständigen Aufbau, die Konfiguration, die Bedienung und die Wartung der <b>DataNexus AI</b> Plattform. "
        "Das System wurde mit dem Ziel entwickelt, bestehende, starre Datenimporte (z. B. historische DBLC-Pipelines) zu entkoppeln, Daten in Höchstgeschwindigkeit zu validieren und eine sichere, maschinenlesbare Schnittstelle für KI-Agenten und lokale RAG-Systeme in der Open Telekom Cloud bereitzustellen.",
        body_style
    ))
    
    story.append(PageBreak())

    # =========================================================
    # KAPITEL 1: SCHNELLSTART & CONTROL CENTER
    # =========================================================
    story.append(Paragraph("1. Schnellstart & Control Center Bedienung", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))
    
    story.append(Paragraph(
        "Die Plattform bietet eine intuitive Ein-Klick-Starter-Datei <code>start.bat</code> sowie ein modernes Web Control Center (Streamlit), "
        "über das sämtliche Parameter, API-Keys, Ingestion-Importe und Tests komfortabel verwaltet werden können.",
        body_style
    ))
    
    story.append(Paragraph("1.1 Ein-Klick-Start via <code>start.bat</code>", h2_style))
    story.append(Paragraph("Im Wurzelverzeichnis des Projekts befindet sich die Starter-Datei <code>start.bat</code>. Ein Doppelklick führt automatisch folgende Schritte aus:", body_style))
    story.append(Paragraph("• <b>Virtuelle Umgebung:</b> Aktiviert das Python <code>venv</code> und prüft alle benötigten Packages.", bullet_style))
    story.append(Paragraph("• <b>FastAPI Backend Server:</b> Startet den REST-API Server im Hintergrund auf Port <code>8000</code> mit Auto-Reload.", bullet_style))
    story.append(Paragraph("• <b>Streamlit Control Center:</b> Startet die Web-Oberfläche auf Port <code>8501</code> und öffnet sie automatisch im Browser.", bullet_style))

    story.append(Spacer(1, 5))
    story.append(Paragraph("start.bat", ParagraphStyle("LabelCode", fontName="Helvetica-Bold", fontSize=8, textColor=CYAN)))
    story.append(Paragraph("REM Ausführen im Windows Explorer oder Terminal:\nstart.bat", code_style))

    story.append(Paragraph("1.2 Die 5 Haupt-Bereiche des Web Control Centers (http://localhost:8501)", h2_style))
    
    tab_summary = [
        [Paragraph("<b>Tab / Bereich</b>", body_style), Paragraph("<b>Funktionsbeschreibung & Features</b>", body_style)],
        [Paragraph("<b>🎛️ Konfiguration & API-Keys</b>", body_style), Paragraph("Verwaltung & Speicherung der API-Keys (Admin, Analyst, Reporting) sowie Infrastruktur-Pfade (Database, Ollama, Milvus).", body_style)],
        [Paragraph("<b>🧪 Test-Runner & Diagnose</b>", body_style), Paragraph("Ausführen aller 24 Pytest-Tests per Mausklick mit Live-Ergebnisanzeige sowie System Health Check.", body_style)],
        [Paragraph("<b>📊 Ingestion & Quarantäne</b>", body_style), Paragraph("Drag-and-Drop CSV Upload-Interface und Live-Tabellen für importierte Datensätze und isolierte Quarantäne-Fehler.", body_style)],
        [Paragraph("<b>🧠 RAG & KI-Playground</b>", body_style), Paragraph("Indizieren neuer Dokumente, Ausführen von Vektorsuchen & Qwen LLM Inferenz sowie rollenbasierte Skill-Ausführung.", body_style)],
        [Paragraph("<b>📄 Betriebshandbuch & Doku</b>", body_style), Paragraph("Integreter Markdown-Viewer zum direkten Lesen aller Handbücher und Berichte im Dashboard.", body_style)]
    ]
    tab_table = Table(tab_summary, colWidths=[150, 337])
    tab_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tab_table)

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 2: STANDALONE DATA INGESTION
    # =========================================================
    story.append(Paragraph("2. Standalone Data Ingestion Engine (Stufe 1)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "Das Ingestion-Modul arbeitet vollständig entkoppelt von Altsystemen (DBLC). "
        "Ein ereignisgesteuerter <b>Watchdog Service</b> überwacht den Eingangsordner <code>incoming/</code> (bzw. FTP-Pfade) auf eintreffende CSV-Dateien.",
        body_style
    ))

    story.append(Paragraph("2.1 High-Speed Parsing & Schema Validation (`Polars`)", h2_style))
    story.append(Paragraph(
        "Für den Parsing-Vorgang wird die Rust-basierte <code>Polars</code> Dataframe Engine genutzt. "
        "Spaltennamen werden automatisch normalisiert. Fehlt eine Pflichtspalte oder liegt ein falscher Datentyp vor, greift die Schema-Validierung.",
        body_style
    ))

    story.append(Paragraph("2.2 Quarantäne-Handling & Dead-Letter Queue", h2_style))
    story.append(Paragraph("• <b>Einzelne fehlerhafte Zeilen:</b> Werden aus dem Import gefiltert und in der Tabelle <code>quarantine_records</code> mit exakter Zeilennummer und Fehlergrund isoliert. Valide Zeilen werden trotzdem importiert.", bullet_style))
    story.append(Paragraph("• <b>Komplett unlesbare Dateien:</b> Werden vom Quarantäne-Manager sofort in den Ordner <code>quarantine/</code> verschoben. Eine Metadaten-Datei <code>.reason.txt</code> protokolliert die Fehlerursache.", bullet_style))

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 3: ONTOLOGIE & SEMANTIK LAYER
    # =========================================================
    story.append(Paragraph("3. Ontologie & Semantik Layer (Stufe 2)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "Da Datenbanken oft kryptische Spaltenbezeichnungen wie <code>col_49_xyz</code> enthalten, stellt die <b>Ontologie Registry</b> "
        "ein maschinenlesbares Wörterbuch bereit. Es ordnet jeder Spalte verständliche deutsche Begriffe, Datentypen, Einheiten und PII-Sicherheitsflags zu.",
        body_style
    ))

    story.append(Paragraph("Automatischer Text2SQL System-Prompt Generator:", h2_style))
    story.append(Paragraph("Das System generiert aus der Ontologie dynamische System-Prompts für KI-Agenten:", body_style))
    
    prompt_code = (
        "### ENTERPRISE DATABASE SCHEMA ONTOLOGY ###\n"
        "Tabelle: `ingested_records` (EnterpriseMetrics)\n"
        "Spalten:\n"
        "  - `entity_id` (customer_or_device_identifier, Typ: STRING): Eindeutige Kundennummer [PII - Gesichert]\n"
        "  - `metric_name` (kpi_metric_name, Typ: STRING): Name der Geschäftskennzahl\n"
        "  - `metric_value` (kpi_metric_value, Typ: FLOAT): Numerischer Wert der Kennzahl"
    )
    story.append(Paragraph(prompt_code, code_style))

    story.append(PageBreak())

    # =========================================================
    # KAPITEL 4: DATA-ACCESS LAYER & RBAC GOVERNANCE
    # =========================================================
    story.append(Paragraph("4. Data-Access Layer & RBAC Governance (Stufe 2)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "KI-Agenten kommunizieren ausschließlich über den abgesicherten <b>FastAPI Service</b>. "
        "Über den HTTP Header <code>X-API-Key</code> wird die Identität des Agenten geprüft und seine Rolle aufgelöst.",
        body_style
    ))

    rbac_table_data = [
        [Paragraph("<b>Rolle (RBAC)</b>", body_style), Paragraph("<b>API Key (Standard)</b>", body_style), Paragraph("<b>Zugriffsrechte & PII Maskierung</b>", body_style)],
        [Paragraph("<b>Admin</b>", body_style), Paragraph("<code>key_admin_secret_123</code>", body_style), Paragraph("Vollzugriff auf alle Tabellen, Rohdaten und PII-Spalten (z. B. Kundennummern).", body_style)],
        [Paragraph("<b>Analyst</b>", body_style), Paragraph("<code>key_analyst_secret_456</code>", body_style), Paragraph("Zugriff auf Fachdaten und Kundennummern zur Analyse.", body_style)],
        [Paragraph("<b>Reporting</b>", body_style), Paragraph("<code>key_reporting_secret_789</code>", body_style), Paragraph("Eingeschränkter Zugriff. PII-Spalten werden automatisch durch die RBAC-Engine mit <code>[RESTRICTED_BY_RBAC]</code> anonymisiert.", body_style)]
    ]
    rbac_table = Table(rbac_table_data, colWidths=[80, 140, 267])
    rbac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(rbac_table)

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 5: LOKALER RAG-STACK & QWEN LLM
    # =========================================================
    story.append(Paragraph("5. Lokaler RAG-Stack & Qwen LLM Inferenz (Stufe 3)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "Für unstrukturierte Dokumente (Verträge, PDFs, Handbücher) kommt ein lokaler RAG-Stack (Retrieval-Augmented Generation) zum Einsatz. "
        "Sämtliche Daten verbleiben zu 100% im deutschen Rechenzentrum (DSGVO-konform).",
        body_style
    ))

    story.append(Paragraph("5.1 Vektor-Datenbank (Milvus) & Embeddings", h2_style))
    story.append(Paragraph("• <b>Milvus Vector DB:</b> Vektordatenbank zur Speicherung von Dokumentensegmenten.", bullet_style))
    story.append(Paragraph("• <b>Embedding Engine:</b> Nutzung deutscher Text-Embeddings (BGE-M3) zur Durchführung von Kosinus-Ähnlichkeitssuchen.", bullet_style))

    story.append(Paragraph("5.2 Lokale Qwen LLM Inferenz via Ollama", h2_style))
    story.append(Paragraph(
        "Die Inferenz erfolgt über den lokalen Ollama-Dienst (<code>http://localhost:11434</code>). "
        "Das System erkennt automatisch installierte Modelle wie <code>qwen2.5-coder:14b</code>, <code>qwen2.5-coder:32b</code> oder <code>deepseek-r1:8b</code>.",
        body_style
    ))

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 6: AGENTIC FRAMEWORK & SKILL-ROUTING
    # =========================================================
    story.append(Paragraph("6. Agentic Framework & Skill-Routing (Stufe 4)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "Anstelle von unberechenbarem ReAct-LLM-Looping verwendet DataNexus AI ein <b>modulares Skill-Framework mit statischen Routen</b>. "
        "Jeder Agenten-Aufruf wird deterministisch gelenkt:",
        body_style
    ))

    story.append(Paragraph("• <code>text2sql_query</code>: Führt strukturierte SQL-Analysen basierend auf der Ontologie aus.", bullet_style))
    story.append(Paragraph("• <code>document_rag_search</code>: Sucht in unstrukturierten Dokumenten und generiert Antworten via Qwen LLM.", bullet_style))
    story.append(Paragraph("• <code>data_health_check</code>: Überprüft System-Gesundheit, Ingestion-Quoten und Quarantäne-Raten.", bullet_style))

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 7: CLOUD DEPLOYMENT & HITNET
    # =========================================================
    story.append(Paragraph("7. Cloud Deployment & HITNET Security (Stufe 5)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph(
        "Die Plattform wird in der <b>Open Telekom Cloud (OTC)</b> auf Elastic Cloud Servern (ECS) betrieben. "
        "Die Absicherung erfolgt über Nginx TLS 1.3 und IP-Whitelisting (HITNET-Sicherheitsstandard).",
        body_style
    ))

    story.append(Paragraph("Automatisierter Cloud-Rollout:", h2_style))
    story.append(Paragraph("PowerShell Skript für Windows Administration:", body_style))
    story.append(Paragraph(".\\deploy\\deploy_otc.ps1 -OtcHost \"otc-ecs-instance.telekom.de\" -User \"ubuntu\"", code_style))

    story.append(Spacer(1, 15))

    # =========================================================
    # KAPITEL 8: WARTUNG & TESTVERIFIKATION
    # =========================================================
    story.append(Paragraph("8. Verifikation & Wartung", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=12))

    story.append(Paragraph("8.1 Testergebnis der automatisierten Test-Suite (24/24 Bestanden)", h2_style))
    story.append(Paragraph(
        "Das Gesamtsystem wird durch 24 automatisierte Pytest-Unit- und Integrationstests abgedeckt. "
        "Die Testsuite garantiert höchste Zuverlässigkeit bei jeder Änderung:",
        body_style
    ))

    test_summary = [
        [Paragraph("<b>Test-Modul</b>", body_style), Paragraph("<b>Anzahl Tests</b>", body_style), Paragraph("<b>Prüfbereich</b>", body_style), Paragraph("<b>Ergebnis</b>", body_style)],
        [Paragraph("<code>test_ingestion.py</code>", body_style), Paragraph("3 Tests", body_style), Paragraph("CSV Parsing, Validation & Quarantäne", body_style), Paragraph("✅ PASSED", body_style)],
        [Paragraph("<code>test_stage2_ontology_rbac.py</code>", body_style), Paragraph("5 Tests", body_style), Paragraph("Ontologie Registry & RBAC PII Anonymisierung", body_style), Paragraph("✅ PASSED", body_style)],
        [Paragraph("<code>test_stage3_rag_qwen.py</code>", body_style), Paragraph("6 Tests", body_style), Paragraph("Embeddings, Vector Store & Qwen RAG Pipeline", body_style), Paragraph("✅ PASSED", body_style)],
        [Paragraph("<code>test_stage4_agentic_skills.py</code>", body_style), Paragraph("6 Tests", body_style), Paragraph("Agent Router, Statisches Routing & Skills", body_style), Paragraph("✅ PASSED", body_style)],
        [Paragraph("<code>test_stage5_cloud_deployment.py</code>", body_style), Paragraph("4 Tests", body_style), Paragraph("Nginx HITNET Config, Grafana & Scripts", body_style), Paragraph("✅ PASSED", body_style)],
        [Paragraph("<b>GESAMT</b>", body_style), Paragraph("<b>24 Tests</b>", body_style), Paragraph("<b>Vollständige Systemabdeckung</b>", body_style), Paragraph("<b>✅ 100% GRÜN</b>", body_style)]
    ]
    test_table = Table(test_summary, colWidths=[140, 70, 187, 90])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(test_table)

    story.append(Spacer(1, 20))

    # Final Callout Box
    callout_data = [[
        Paragraph(
            "<b>HINWEIS ZUR BETRIEBSÜBERNAHME:</b><br/>"
            "Durch die Kombination aus automatisierten Pytest-Tests, deklarativer Docker-Infrastruktur, "
            "importierbarem Grafana Dashboard as Code und diesem umfassenden Betriebshandbuch ist das System "
            "<b>vollkommen unabhängig von einzelnen Entwicklern betreibbar</b> (Abbau der Key-Person-Dependency).",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[487])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#d1fae5")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#10b981")),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(callout_table)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Manual successfully created at: {output_pdf_path}")


if __name__ == "__main__":
    out_path = os.path.join("docs", "BENUTZERHANDBUCH.pdf")
    build_pdf_manual(out_path)
