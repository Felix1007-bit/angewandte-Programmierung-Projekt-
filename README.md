# Angewandte Programmierung – Projekt

Eine vollständige REST-API mit FastAPI, SQLModel und Streamlit-Frontend, entwickelt im Kurs "Angewandte Programmierung" (Day 1–7).

---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Technologien](#technologien)
3. [Setup & Installation](#setup--installation)
4. [Projektstruktur](#projektstruktur)
5. [main.py – Code-Erklärung](#mainpy--code-erklärung)
6. [frontend.py – Code-Erklärung](#frontendpy--code-erklärung)
7. [Testdateien](#testdateien)
8. [API-Endpoints Übersicht](#api-endpoints-übersicht)

---

## Projektübersicht

Dieses Projekt ist eine vollständige Webanwendung bestehend aus:

- **Backend**: FastAPI-REST-API mit SQLite-Datenbank
- **Frontend**: Streamlit-Webanwendung, die die API aufruft
- **Tests**: Automatisierte Tests mit `requests` (kein pytest nötig)

Die API verwaltet Notizen (`Notes`), Tags und Kurse (`Courses`). Notizen können nach Kategorie, Schlagwort und Datum gefiltert werden.

---

## Technologien

| Technologie | Version | Zweck |
|-------------|---------|-------|
| **FastAPI** | ≥ 0.136 | Web-Framework für REST-API |
| **SQLModel** | ≥ 0.0.22 | ORM für SQLite-Datenbank (kombiniert SQLAlchemy + Pydantic) |
| **Pydantic v2** | (via FastAPI) | Eingabe-Validierung und Datenmodelle |
| **Streamlit** | ≥ 1.57 | Web-Frontend ohne HTML/CSS/JS |
| **SQLite** | (built-in) | Datenbankdatei `notes.db` |
| **uv** | aktuell | Paketmanager und Task-Runner |

---

## Setup & Installation

### Voraussetzungen

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installiert

### Installation

```bash
# Repository klonen
git clone <dein-repo-url>
cd angewandte-Programmierung-Projekt-

# Abhängigkeiten installieren
uv sync
```

### Starten

```bash
# Terminal 1 – FastAPI-Backend starten
uv run fastapi dev main.py
# → läuft auf http://127.0.0.1:8000
# → API-Dokumentation: http://127.0.0.1:8000/docs

# Terminal 2 – Streamlit-Frontend starten
uv run streamlit run frontend.py
# → läuft auf http://localhost:8501
```

### Tests ausführen

```bash
# Eigene Validierungstests (Day 5 Hausaufgabe)
uv run python test_validation.py

# Professor-Testsuite (70 Tests)
uv run python test_main_professor.py

# Mit pytest
uv run pytest test_main.py -v
```

---

## Projektstruktur

```
angewandte-Programmierung-Projekt-/
│
├── main.py                  # FastAPI-Backend (Day 1–6)
├── frontend.py              # Streamlit-Frontend (Day 7)
│
├── test_main.py             # Allgemeine API-Tests
├── test_validation.py       # Pydantic-Validierungstests (Day 5)
├── test_main_professor.py   # Professor-Testsuite (70 Tests)
│
├── class_based_decorator.py # Klassen-basierter Decorator (Day 6 Übung)
├── pyproject.toml           # Projektabhängigkeiten (uv)
├── notes.db                 # SQLite-Datenbankdatei (wird automatisch erstellt)
└── README.md                # Diese Datei
```

---

## main.py – Code-Erklärung

### 1. Imports und Datenbanksetup

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator, ConfigDict, Field as PydanticField
from sqlmodel import SQLModel, Field as SQLField, Session, create_engine, select
from datetime import datetime, timezone
from typing import Optional, Annotated, TypeAlias
```

- **`asynccontextmanager`**: Ermöglicht den `lifespan`-Kontext-Manager – wird beim Start der App ausgeführt, um die Datenbank zu initialisieren.
- **`HTTPException`**: Wirft HTTP-Fehler wie 404 oder 409 mit einer Fehlermeldung.
- **`Depends`**: FastAPIs Dependency-Injection – `SessionDep` stellt automatisch eine Datenbankverbindung bereit.
- **`TypeAlias`**: Notwendig in Python 3.12, damit Pylance `SessionDep` korrekt als Typ-Alias erkennt.

```python
DATABASE_URL = "sqlite:///./notes.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
```

- `sqlite:///./notes.db` → SQLite-Datei `notes.db` im aktuellen Verzeichnis.
- `check_same_thread=False` → nötig für FastAPI, da mehrere Threads die Verbindung gleichzeitig nutzen.

```python
SessionDep: TypeAlias = Annotated[Session, Depends(get_session)]
```

- Kurzform für Dependency-Injection: Jede Route-Funktion mit `session: SessionDep` bekommt automatisch eine aktive Datenbankverbindung.

---

### 2. Lifespan – App-Start

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
```

- Wird einmalig beim Start der App ausgeführt.
- `create_db_and_tables()` erstellt alle SQLite-Tabellen, falls sie noch nicht existieren.
- `yield` markiert den Punkt, ab dem die App läuft. Code nach `yield` würde beim Shutdown ausgeführt.

---

### 3. Datenbankmodell – NoteDB

```python
class NoteDB(SQLModel, table=True):
    __tablename__ = "note"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str
    content: str
    category: str
    tags_json: str = SQLField(default="[]")
    created_at: str
```

- `table=True` → SQLModel erstellt daraus eine echte SQLite-Tabelle.
- `id=None` mit `primary_key=True` → SQLite vergibt die ID automatisch (Auto-Increment).
- `tags_json` speichert Tags als JSON-String, z.B. `'["work", "meeting"]'`, weil SQLite keine nativen Arrays kennt. Beim Lesen wird er mit `json.loads()` zurück in eine Liste umgewandelt.

---

### 4. Pydantic-Eingabemodelle (Validierung)

#### NoteCreate – Vollständige Validierung

```python
class NoteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = PydanticField(min_length=3, max_length=100)
    content: str = PydanticField(min_length=1, max_length=10_000)
    category: str = PydanticField(min_length=2, max_length=30)
    tags: list[str] = PydanticField(default_factory=list, max_length=10)
```

- **`str_strip_whitespace=True`**: Führende/abschließende Leerzeichen werden automatisch entfernt.
- **`extra="forbid"`**: Unbekannte Felder im Request-Body geben 422 zurück – schützt vor Tippfehlern.
- **`min_length`/`max_length`**: Pydantic prüft die Länge automatisch; bei Verstoß → 422 Unprocessable Entity.

```python
@field_validator("title")
@classmethod
def title_not_only_whitespace(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("Titel darf nicht nur aus Leerzeichen bestehen")
    return v
```

- **`@field_validator`**: Pydantic v2-Decorator für feldbezogene Validierungslogik.
- `@classmethod` ist in Pydantic v2 Pflicht.
- `ValueError` → FastAPI wandelt das automatisch in eine 422-Antwort mit Fehlerbeschreibung um.

```python
@field_validator("category")
@classmethod
def category_must_be_valid(cls, v: str) -> str:
    normalized = v.strip().lower()
    if normalized not in ALLOWED_CATEGORIES:
        raise ValueError(...)
    return normalized   # speichert immer Kleinbuchstaben
```

- Normalisiert vor dem Speichern: `"WORK"` → `"work"`.

```python
@field_validator("tags")
@classmethod
def clean_tags(cls, raw: list[str]) -> list[str]:
    cleaned, seen = [], set()
    for tag in raw:
        t = tag.strip().lower()
        if not t: raise ValueError("...")         # leerer Tag
        if len(t) < 2: raise ValueError("...")    # zu kurz
        if t in seen: continue                    # Duplikat überspringen
        seen.add(t)
        cleaned.append(t)
    return cleaned
```

- Trimmt, normalisiert, entfernt Duplikate und prüft Mindestlänge für jeden Tag.

#### NoteUpdate – Partielles Update (PATCH)

```python
class NoteUpdate(BaseModel):
    title: Optional[str] = PydanticField(default=None, min_length=3, max_length=100)
    content: Optional[str] = PydanticField(default=None, ...)
    category: Optional[str] = PydanticField(default=None, ...)
    tags: Optional[list[str]] = PydanticField(default=None, ...)
```

- Alle Felder sind `Optional` mit `default=None` → PATCH darf einen leeren Body `{}` schicken, ohne Fehler.
- Constraints (min_length etc.) gelten weiterhin, sobald ein Feld angegeben wird.

---

### 5. Notes Endpoints

#### POST /notes – Notiz erstellen

```python
@app.post("/notes", status_code=201)
def create_note(note: NoteCreate, session: SessionDep) -> NoteResponse:
    db_note = NoteDB(
        title=note.title,
        content=note.content,
        category=note.category,
        tags_json=json.dumps(note.tags),
        created_at=datetime.now(timezone.utc).isoformat()
    )
    session.add(db_note)
    session.commit()
    session.refresh(db_note)   # lädt id aus der Datenbank nach
    return db_to_note(db_note)
```

- FastAPI parsed den JSON-Body automatisch in `NoteCreate` und validiert ihn.
- `session.refresh()` ist nötig, damit `id` nach dem INSERT befüllt ist.
- `db_to_note()` konvertiert das Datenbankmodell in das API-Antwortmodell (Trennung von Datenbankstruktur und API-Schnittstelle).

#### GET /notes – Notizen mit Filtern

```python
@app.get("/notes")
def list_notes(
    session: SessionDep,
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None
) -> list[NoteResponse]:
```

- Query-Parameter werden automatisch aus der URL gelesen: `/notes?category=work&search=meeting`
- `Optional[datetime]` → FastAPI prüft das Datumsformat automatisch; ungültige Werte → 422.
- Zeitzone-Handling: gespeicherte Timestamps werden mit UTC verglichen, unabhängig von der lokalen Zeitzone.

#### GET /notes/stats – WICHTIG: Reihenfolge

```python
@app.get("/notes/stats")   # Muss VOR /notes/{note_id} stehen!
def get_notes_stats(session: SessionDep):
```

- FastAPI matcht Routen in der Reihenfolge, in der sie definiert sind.
- Würde `/notes/{note_id}` zuerst stehen, würde ein GET `/notes/stats` als `note_id="stats"` interpretiert → 422.

#### PUT vs. PATCH

- **PUT** (`NoteCreate`): Erwartet alle Pflichtfelder → ersetzt die Notiz vollständig.
- **PATCH** (`NoteUpdate`): Alle Felder optional → aktualisiert nur was übergeben wurde.

---

### 6. Tags Endpoints

```python
@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str, session: SessionDep):
    notes = session.exec(select(NoteDB)).all()
    return [db_to_note(n) for n in notes if tag_name.lower() in json.loads(n.tags_json)]
```

- `tag_name.lower()` → Case-insensitive Suche: `/tags/WORK/notes` findet Notizen mit Tag `"work"`.
- `json.loads(n.tags_json)` → JSON-String wird in Python-Liste umgewandelt, dann mit `in` geprüft.

```python
class TagCreate(BaseModel):
    name: str = PydanticField(
        min_length=2,
        max_length=30,
        pattern=r"^[a-z0-9-]+$",
    )
```

- **`pattern`**: Regex-Validierung – nur Kleinbuchstaben, Ziffern und Bindestriche erlaubt. Großbuchstaben oder Leerzeichen → 422.

---

### 7. Course Endpoints (Day 4)

```python
class CourseDB(SQLModel, table=True):
    code: str = SQLField(unique=True, index=True)
```

- `unique=True` → SQLite verhindert doppelte Kurscodes auf Datenbankebene.
- `index=True` → Erstellt einen Datenbankindex für schnelle Abfragen auf `code`.

```python
@app.post("/courses", status_code=201)
def create_course(course: CourseCreate, session: SessionDep):
    for existing in all_courses:
        if existing.code.upper() == course.code.upper():   # case-insensitiv
            raise HTTPException(status_code=409, ...)
```

- **409 Conflict** (statt 422): Die Eingabe ist valide, aber ein Duplikat existiert bereits in der Datenbank.

---

## frontend.py – Code-Erklärung

### Wie Streamlit funktioniert

Streamlit führt das gesamte Python-Skript bei **jeder Benutzerinteraktion** neu aus. Das bedeutet:
- Variablen werden bei jedem Klick neu initialisiert.
- `st.session_state` ist der einzige Ort, der zwischen Reruns Daten erhält.

### Hilfsfunktionen

```python
def load_notes() -> list[dict]:
    try:
        response = requests.get(f"{API_BASE}/notes", timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        pass
    return None  # None = Verbindungsfehler (nicht leere Liste!)
```

- `timeout=3`: Wartet max. 3 Sekunden – verhindert, dass die App ewig hängt.
- `except ConnectionError`: Verhindert Absturz, wenn der FastAPI-Server nicht läuft.
- Rückgabe `None` signalisiert dem UI: Verbindung fehlgeschlagen (leere Liste `[]` würde bedeuten: Server läuft, aber keine Notizen vorhanden).

### Session State Pattern

```python
if "say_no_text" not in st.session_state:
    st.session_state["say_no_text"] = request_no()
```

- **Einmalige Initialisierung**: Der API-Call passiert nur beim allerersten Laden der Seite.
- Danach bleibt der Wert erhalten, auch wenn Streamlit die Seite neu rendert.

### Tab-Layout

```python
tab1, tab2 = st.tabs(["📋 Alle Notizen", "➕ Neue Notiz erstellen"])

with tab1:
    ...   # Code für Tab 1
with tab2:
    ...   # Code für Tab 2
```

- `st.tabs()` erstellt eine Tab-Navigation. Der `with`-Block enthält den Inhalt des jeweiligen Tabs.

### Formular für neue Notiz

```python
with st.form("new_note_form", clear_on_submit=True):
    title = st.text_input("Titel *")
    content = st.text_area("Inhalt *", height=150)
    category = st.selectbox("Kategorie *", CATEGORIES)
    tags_input = st.text_input("Tags (kommagetrennt)")
    submitted = st.form_submit_button("✅ Notiz erstellen", type="primary")
```

- **`st.form`**: Gruppert Eingaben – Streamlit führt keinen Rerun aus, solange der Nutzer tippt.
- **`clear_on_submit=True`**: Alle Felder werden nach dem Absenden zurückgesetzt.
- **`submitted`**: Ist `True` genau einmal, direkt nach dem Klick auf den Submit-Button.

```python
if submitted:
    tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
```

- List-Comprehension: `"urgent, Meeting, projekt"` → `["urgent", "meeting", "projekt"]`
- `if t.strip()` → leere Einträge (z.B. doppeltes Komma) werden übersprungen.

---

## Testdateien

### test_validation.py

Testet alle Pydantic-Validierungsregeln direkt gegen die laufende API:

| Gruppe | Was wird getestet |
|--------|-------------------|
| Field Constraints | Titel zu kurz/leer/nur Leerzeichen; Inhalt leer; zu viele Tags |
| Category Validator | Unbekannte Kategorie → 422; Großschreibung wird normalisiert → 201 |
| Tag Validator | Tags trimmen/normalisieren/deduplizieren; leer/zu kurz → 422 |
| Extra Fields | Unbekannte Felder im Body → 422 (`extra="forbid"`) |
| Work-Notizen | `category="work"` ohne und mit "work"-Tag → beide 201 |
| Tag-Endpoint | `POST /tags` mit Großbuchstaben, Leerzeichen, zu kurz → 422 |
| PATCH Validation | Leerer Body → 200; ungültiger Titel/Kategorie → 422 |

### test_main_professor.py

70-Test-Suite des Professors – testet alle Endpoints vollständig:
- Komplettes CRUD für Notizen
- Alle Filter-Kombinationen (`category`, `search`, `tag`, `created_after`, `created_before`)
- Statistik-Endpoint
- Tag- und Kategorie-Endpoints
- Edge Cases: 404 bei ungültiger ID, 409 bei Duplikaten, 422 bei ungültigen Eingaben

---

## API-Endpoints Übersicht

### Notes

| Methode | URL | Beschreibung | Erfolgs-Status |
|---------|-----|--------------|----------------|
| `GET` | `/notes` | Alle Notizen (optionale Filter) | 200 |
| `POST` | `/notes` | Neue Notiz erstellen | 201 |
| `GET` | `/notes/stats` | Statistiken (Anzahl, Top-Tags, Kategorien) | 200 |
| `GET` | `/notes/{id}` | Einzelne Notiz per ID | 200 / 404 |
| `PUT` | `/notes/{id}` | Notiz vollständig ersetzen | 200 / 404 |
| `PATCH` | `/notes/{id}` | Notiz partiell aktualisieren | 200 / 404 |
| `DELETE` | `/notes/{id}` | Notiz löschen | 204 / 404 |

#### Filter-Parameter für `GET /notes`

| Parameter | Typ | Beispiel |
|-----------|-----|---------|
| `category` | string | `?category=work` |
| `search` | string | `?search=meeting` |
| `tag` | string | `?tag=urgent` |
| `created_after` | ISO 8601 | `?created_after=2025-01-01T00:00:00` |
| `created_before` | ISO 8601 | `?created_before=2025-12-31T23:59:59` |

### Tags

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| `GET` | `/tags` | Alle einzigartigen Tags (aus Notizen) |
| `GET` | `/tags/{name}/notes` | Alle Notizen mit diesem Tag (case-insensitiv) |
| `POST` | `/tags` | Tag mit strikter Validierung erstellen |

### Categories

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| `GET` | `/categories` | Alle genutzten Kategorien |
| `GET` | `/categories/{name}/notes` | Alle Notizen dieser Kategorie |

### Courses

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| `POST` | `/courses` | Neuen Kurs erstellen |
| `GET` | `/courses` | Alle Kurse (Filter: `semester`, `min_ects`) |
| `GET` | `/courses/{id}` | Kurs per ID |

### Sonstiges

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| `GET` | `/` | Hello World |
| `GET` | `/status` | API-Status |
| `GET` | `/about` | Projektinfo |
| `GET` | `/square/{n}` | Quadratzahl berechnen |
| `GET` | `/double/{n}` | Verdoppeln |
| `GET` | `/student` | Studenteninformationen |

---

## Erlaubte Kategorien

```
work | personal | school | ideas | general
```

## Tag-Format (`POST /tags`)

- Regex: `^[a-z0-9-]+$`
- Nur Kleinbuchstaben, Ziffern und Bindestriche
- Mindestens 2, maximal 30 Zeichen
- Keine Leerzeichen, keine Großbuchstaben

---

*Projekt aus dem Kurs "Angewandte Programmierung" – Day 1 bis Day 7*
