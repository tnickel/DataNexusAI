# DataNexus AI – Anforderungs- und Leistungsspezifikation

Dieses Dokument übersetzt und strukturiert die technischen Anforderungen des Projekts **DataNexus AI** (Standalone Data Ingestion, Semantic Layer, Agentic Framework & RAG auf Open Telekom Cloud) in klare, verständliche Funktionsbausteine auf Deutsch.

---

## 1. Executive Summary & Zielsetzung

Ziel des Projekts ist das Design und die Implementierung einer **eigenständigen, entkoppelten Plattform für Datenverarbeitung und KI-Agenten**. 

Das System löst bestehende Monolithen (DBLC-Pipeline) ab und stellt eine zukunftssichere Infrastruktur bereit:
- **Daten-Ingestion**: Standalone & hochperformant (FTP → CSV → Datenbank).
- **Semantik & Governance**: Maschinenlesbare Ontologie für LLMs mit feingranularem Zugriffsschutz.
- **Agentic Framework**: Skill-basiertes Routing mit hybrider Suche (SQL + Vektor-DB / Milvus).
- **Lokale KI-Inferenz**: RAG-Pipeline mit deutschen Embeddings und lokalen Qwen LLM-Modellen.
- **Sichere Cloud-Infrastruktur**: Deployment in der Open Telekom Cloud (OTC) über HITNET mit Grafana-Monitoring.

---

## 2. Detaillierte Funktionsbereiche & Anforderungen

### 2.1. Stand-Alone Data-Ingestion Komponente
* **Entkopplung**: Vollständige Trennung von der bestehenden DBLC-Pipeline (Legacy FTP/CSV-Verarbeitung).
* **Automatisierter Datenimport**: 
  * Überwachung von FTP-Verzeichnissen (FTP Watchdog / Event Trigger).
  * Robustes Parsing von CSV-Dateien (Parsing, Typ-Konvertierung, Validierung mit Polars / Pandas).
  * Effizientes Schreiben in die Zieldatenbank (PostgreSQL / ClickHouse / MySQL).
* **Fehlerbehandlung & Logging**: Automatische Quarantäne fehlerhafter Dateien, Benachrichtigungen und lückenloses Auditing.

### 2.2. OTC Cloud-Architektur & Datenbank-Entscheidungen
* **Plattform-Evaluierung (Open Telekom Cloud - OTC)**:
  * Vergleich von **Database-as-a-Service (DBaaS)** vs. **Self-Hosted** (z. B. PostgreSQL/ClickHouse auf OTC Elastic Cloud Servern).
  * Bewertung hinsichtlich **Kosten**, **Skalierbarkeit** und **Betriebsaufwand**.
* **Performance-Optimierung**:
  * Konzeption von Indexierungsstrategien (B-Tree, GIN, Partitionierung) für schnelle analytische Abfragen durch KI-Agenten.
* **Infrastructure-as-Code (IaC)**:
  * Bereitstellung von Dockerfiles, `docker-compose.yml` oder Terraform-Skripten für reproduzierbare Deployments.

### 2.3. Ontologie / Semantik-Schicht & Data-Access-Layer
* **Semantische Metadaten-Schicht (Ontologie)**:
  * Erstellung maschinenlesbarer Beschreibungen (z. B. Pydantic-Modelle, JSON-Schema oder OWL/RDF) aller Tabellen, Spalten und Beziehungen.
  * Ziel: LLMs und KI-Agenten verstehen die Bedeutung der Daten ohne menschliche Rückfragen.
* **Data-Access Layer & Access Control**:
  * Zwischenschaltung einer sicheren API-Schicht (FastAPI / Service-Layer) zwischen Datenbank und KI-Agenten.
  * Rollenbasierte Zugriffskontrolle (RBAC) und Token-Governance: Agenten erhalten strikt nur Zugriff auf freigegebene Daten.

### 2.4. Agentic Framework & Skill-basiertes Routing
* **Architektur-Evolution**:
  * Weiterentwicklung des bestehenden Agenten-Systems hin zu einem **skill-basierten Ansatz**.
  * Ersatz von dynamischem / unvorhersehbarem Routing durch **definierte statische Routen** (deterministische Ausführungsketten).
* **Tooling Integration**:
  * Integration von SQL-Abfragewerkzeugen und Vektor-DB-Tools für hybrides Retrieval (Text2SQL + Vector Search).
* **Standardisierung & Health Checks**:
  * Entwicklung wiederverwendbarer Agenten-Bausteine.
  * Automatisierte Test-Pipelines und kontinuierliche Health-Checks zur Überwachung der Agenten-Verfügbarkeit.

### 2.5. RAG-Stack & Vektor-Suche (Milvus & Qwen LLMs)
* **Vektor-Datenbank**: Anbindung und Konfiguration von **Milvus** für Hochleistungs-Vektorsuche.
* **Chunking & Embedding**:
  * Implementierung passgenauer Chunking-Strategien für strukturierte und unstrukturierte Texte.
  * Integration spezialisierter **deutscher Embedding-Modelle** (z. B. `bge-m3`, `gbert-large` oder `multilingual-e5`).
* **Lokale LLM-Inferenz**:
  * Ausführung von **Qwen LLM-Modellen** direkt auf eigener Infrastruktur (z. B. via vLLM oder Ollama), um höchste Datenschutzanforderungen zu erfüllen.

### 2.6. Sicheres Frontend Deployment (Grafana & HITNET)
* **Dashboard Deployment**: Exporte von Grafana-Dashboards als Code (JSON-Templates) zur automatisierten Bereitstellung.
* **Netzwerksicherheit & HITNET**:
  * Sichere Anbindung der OTC-Ressourcen an das HITNET-Netzwerk des Kunden.
  * Härtung von Reverse-Proxies (Nginx), TLS/SSL-Verschlüsselung, IP-Restriktionen und Isolation.
* **Supply-Chain-Absicherung**: Überprüfung und Härtung von Container-Images und Software-Abhängigkeiten.

### 2.7. Wissenstransfer & Proaktive Technical Consulting
* **Dokumentation**: Erstellung von Architekturdiagrammen (Mermaid), REST-API-Spezifikationen (OpenAPI/Swagger) und Administrator-Runbooks.
* **Abbau der Key-Person-Dependency**: Strukturierter Know-how-Transfer an das interne Kunden-Team, damit das System nach Projektende eigenständig betrieben und erweitert werden kann.

---

## 3. Nicht-funktionale Anforderungen & Qualitätstore

| Anforderung | Beschreibung / Zielvorgabe |
| :--- | :--- |
| **Datenschutz & DSGVO** | 100% DSGVO-konform durch Hosten in deutschen OTC-Rechenzentren und lokale LLM-Inferenz ohne externe Drittanbieter-APIs. |
| **Lokale Testbarkeit** | Das Gesamtsystem muss zu 100% lokal via Docker Compose / Ollama simulierbar sein, bevor ein Cloud-Deployment erfolgt. |
| **Modulariät** | Jede Komponente (Ingestion, Access Layer, Vector DB, Agent Routing) ist lose gekoppelt und einzeln austauschbar. |
| **Reproduzierbarkeit** | Infrastructure-as-Code und skriptbasiertes Setup aller Services ohne manuelle Server-Klicks. |

---

## 4. Anforderungsprofil & Skillset (Developer / Consultant)

* **Betriebssystem & IDE**: Linux-Erfahrung, Visual Studio Code / Cursor / Claude Code / Antigravity workflows.
* **Methodik**: KI-gestützte Softwareentwicklung (AI-Pair-Programming), systematische Verifikation und sauberes Refactoring.
* **Sprachen & Frameworks**: Python (Polars, Pandas, SQLAlchemy, FastAPI, Pydantic), SQL, Docker, Bash/PowerShell.
