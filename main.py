from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator, model_validator, ConfigDict, Field as PydanticField
from sqlmodel import SQLModel, Field as SQLField, Session, create_engine, select, col
from datetime import datetime, timezone
from typing import Optional, Self, Annotated, TypeAlias
from collections import Counter
import json

# ─────────────────────────────────────────
# Datenbank-Setup (Day 6 – SQLModel + SQLite)
# ─────────────────────────────────────────

DATABASE_URL = "sqlite:///./notes.db"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep: TypeAlias = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# ─────────────────────────────────────────
# App
# ─────────────────────────────────────────

app = FastAPI(
    title="Angewandte Programmierung",
    description="Notes, Tags & Courses API",
    version="2.0.0",
    lifespan=lifespan
)

# ─────────────────────────────────────────
# Day 1 – Klassen-Endpoints
# ─────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Hello World!"}


@app.get("/status")
def get_status():
    return {"status": "online", "version": "0.1.0", "day": 1}


@app.get("/about")
def get_about():
    return {"project": "My First API", "author": "Felix", "course": "Applied Programming"}


# ─────────────────────────────────────────
# Day 1 – Hausaufgaben-Endpoints
# ─────────────────────────────────────────

@app.get("/square/{number}")
def calculate_square(number: int):
    result = number * number
    return {"number": number, "square": result, "calculation": f"{number} × {number} = {result}"}


@app.get("/student")
def get_student():
    return {
        "name": "Felix",
        "semester": 1,
        "course": "Wirtschaftsinformatik",
        "university": "Deine Universität"
    }


@app.get("/double/{number}")
def calculate_double(number: int):
    result = number * 2
    return {"number": number, "double": result, "calculation": f"{number} × 2 = {result}"}


# ─────────────────────────────────────────
# Day 2/3/5 – Note Datenbank-Modell (SQLModel)
# ─────────────────────────────────────────

class NoteDB(SQLModel, table=True):
    """SQLite-Tabelle für Notizen. Tags werden als JSON-String gespeichert."""
    __tablename__ = "note"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str
    content: str
    category: str
    tags_json: str = SQLField(default="[]")   # z.B. '["work", "meeting"]'
    created_at: str


# ─────────────────────────────────────────
# Day 2/3/5 – Note Eingabe-Modelle (Pydantic)
# ─────────────────────────────────────────

ALLOWED_CATEGORIES = {"work", "personal", "school", "ideas", "general"}


class NoteCreate(BaseModel):
    """Eingabe-Modell mit vollständiger Day-5-Validierung."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    title: str = PydanticField(
        min_length=3, max_length=100,
        description="Kurzer Notiztitel (3–100 Zeichen)",
        examples=["Einkaufsliste"]
    )
    content: str = PydanticField(
        min_length=1, max_length=10_000,
        description="Inhalt der Notiz"
    )
    category: str = PydanticField(
        min_length=2, max_length=30,
        description=f"Erlaubte Kategorien: {sorted(ALLOWED_CATEGORIES)}",
        examples=["work"]
    )
    tags: list[str] = PydanticField(
        default_factory=list,
        max_length=10,
        description="Bis zu 10 Tags"
    )

    @field_validator("title")
    @classmethod
    def title_not_only_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Titel darf nicht nur aus Leerzeichen bestehen")
        return v

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in ALLOWED_CATEGORIES:
            raise ValueError(f"category muss eines von {sorted(ALLOWED_CATEGORIES)} sein")
        return normalized

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, raw: list[str]) -> list[str]:
        cleaned, seen = [], set()
        for tag in raw:
            t = tag.strip().lower()
            if not t:
                raise ValueError("Tags dürfen keine leeren Zeichenketten sein")
            if len(t) < 2:
                raise ValueError(f"Tag '{t}' muss mindestens 2 Zeichen haben")
            if t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
        return cleaned



class NoteUpdate(BaseModel):
    """PATCH-Modell: alle Felder optional, Constraints bleiben erhalten."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = PydanticField(default=None, min_length=3, max_length=100)
    content: Optional[str] = PydanticField(default=None, min_length=1, max_length=10_000)
    category: Optional[str] = PydanticField(default=None, min_length=2, max_length=30)
    tags: Optional[list[str]] = PydanticField(default=None, max_length=10)

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().lower()
        if normalized not in ALLOWED_CATEGORIES:
            raise ValueError(f"category muss eines von {sorted(ALLOWED_CATEGORIES)} sein")
        return normalized

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, raw: Optional[list[str]]) -> Optional[list[str]]:
        if raw is None:
            return raw
        cleaned, seen = [], set()
        for tag in raw:
            t = tag.strip().lower()
            if not t:
                raise ValueError("Tags dürfen keine leeren Zeichenketten sein")
            if len(t) < 2:
                raise ValueError(f"Tag '{t}' muss mindestens 2 Zeichen haben")
            if t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
        return cleaned


class NoteResponse(BaseModel):
    """API-Antwort-Modell für Notizen."""
    id: int
    title: str
    content: str
    category: str
    tags: list[str]
    created_at: str


def db_to_note(note: NoteDB) -> NoteResponse:
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=json.loads(note.tags_json),
        created_at=note.created_at
    )


# ─────────────────────────────────────────
# Day 2/3 – Notes Endpoints
# ─────────────────────────────────────────

@app.post("/notes", status_code=201)
def create_note(note: NoteCreate, session: SessionDep) -> NoteResponse:
    """Neue Notiz erstellen."""
    db_note = NoteDB(
        title=note.title,
        content=note.content,
        category=note.category,
        tags_json=json.dumps(note.tags),
        created_at=datetime.now(timezone.utc).isoformat()
    )
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    return db_to_note(db_note)


@app.get("/notes")
def list_notes(
    session: SessionDep,
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None
) -> list[NoteResponse]:
    """Notizen auflisten mit optionalen Filtern."""
    notes = session.exec(select(NoteDB)).all()

    filtered = []
    for note in notes:
        if category and note.category != category:
            continue
        if search:
            s = search.lower()
            if s not in note.title.lower() and s not in note.content.lower():
                continue
        if tag and tag.lower() not in json.loads(note.tags_json):
            continue
        if created_after:
            note_dt = datetime.fromisoformat(note.created_at)
            if note_dt.tzinfo is None:
                note_dt = note_dt.replace(tzinfo=timezone.utc)
            ca = created_after if created_after.tzinfo else created_after.replace(tzinfo=timezone.utc)
            if note_dt < ca:
                continue
        if created_before:
            note_dt = datetime.fromisoformat(note.created_at)
            if note_dt.tzinfo is None:
                note_dt = note_dt.replace(tzinfo=timezone.utc)
            cb = created_before if created_before.tzinfo else created_before.replace(tzinfo=timezone.utc)
            if note_dt > cb:
                continue
        filtered.append(note)

    return [db_to_note(n) for n in filtered]


# WICHTIG: /notes/stats vor /notes/{note_id} definieren!
@app.get("/notes/stats")
def get_notes_stats(session: SessionDep):
    """Statistiken über alle Notizen."""
    notes = session.exec(select(NoteDB)).all()

    categories: dict = {}
    all_tags: list = []
    for note in notes:
        categories[note.category] = categories.get(note.category, 0) + 1
        all_tags.extend(json.loads(note.tags_json))

    tag_counter = Counter(all_tags)
    top_tags = [{"tag": t, "count": c} for t, c in tag_counter.most_common(5)]

    return {
        "total_notes": len(notes),
        "by_category": categories,
        "top_tags": top_tags,
        "unique_tags_count": len(tag_counter)
    }


@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep) -> NoteResponse:
    """Einzelne Notiz per ID abrufen."""
    note = session.get(NoteDB, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    return db_to_note(note)


@app.put("/notes/{note_id}")
def update_note(note_id: int, note_update: NoteCreate, session: SessionDep) -> NoteResponse:
    """Notiz vollständig aktualisieren (alle Felder ersetzen)."""
    note = session.get(NoteDB, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    note.title = note_update.title
    note.content = note_update.content
    note.category = note_update.category
    note.tags_json = json.dumps(note_update.tags)
    session.add(note)
    session.commit()
    session.refresh(note)
    return db_to_note(note)


@app.patch("/notes/{note_id}")
def partial_update_note(note_id: int, note_update: NoteUpdate, session: SessionDep) -> NoteResponse:
    """Notiz partiell aktualisieren (nur übergebene Felder)."""
    note = session.get(NoteDB, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    if note_update.category is not None:
        note.category = note_update.category
    if note_update.tags is not None:
        note.tags_json = json.dumps(note_update.tags)
    session.add(note)
    session.commit()
    session.refresh(note)
    return db_to_note(note)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, session: SessionDep):
    """Notiz löschen. Gibt 204 No Content zurück."""
    note = session.get(NoteDB, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note)
    session.commit()


# ─────────────────────────────────────────
# Day 3 – Tags Endpoints (aus Notizen)
# ─────────────────────────────────────────

@app.get("/tags")
def list_tags(session: SessionDep) -> list[str]:
    """Alle einzigartigen Tags aus allen Notizen."""
    notes = session.exec(select(NoteDB)).all()
    all_tags: set = set()
    for note in notes:
        all_tags.update(json.loads(note.tags_json))
    return sorted(list(all_tags))


@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str, session: SessionDep) -> list[NoteResponse]:
    """Alle Notizen mit einem bestimmten Tag."""
    notes = session.exec(select(NoteDB)).all()
    return [db_to_note(n) for n in notes if tag_name.lower() in json.loads(n.tags_json)]


# ─────────────────────────────────────────
# Day 3 – Categories Endpoints
# ─────────────────────────────────────────

@app.get("/categories")
def list_categories(session: SessionDep) -> list[str]:
    """Alle einzigartigen Kategorien."""
    notes = session.exec(select(NoteDB)).all()
    return sorted(list(set(note.category for note in notes)))


@app.get("/categories/{category_name}/notes")
def get_notes_by_category(category_name: str, session: SessionDep) -> list[NoteResponse]:
    """Alle Notizen einer Kategorie."""
    notes = session.exec(
        select(NoteDB).where(NoteDB.category == category_name)
    ).all()
    return [db_to_note(n) for n in notes]


# ─────────────────────────────────────────
# Day 3 – Query Parameters (Übung)
# ─────────────────────────────────────────

@app.get("/queryparameters")
def query_parameters(param1: Optional[str] = None, param2: Optional[int] = None) -> dict:
    namen = ["Alice", "Bob", "Charlie"]
    if not param1:
        return {"namen": namen}
    return {
        "param1": param1,
        "param2": param2,
        "namen": [n for n in namen if param1 in n]
    }


# ─────────────────────────────────────────
# Day 5 Task 5 – Tag-Modell mit strikter Validierung
# ─────────────────────────────────────────

class TagDB(SQLModel, table=True):
    """SQLite-Tabelle für explizit erstellte Tags mit strenger Validierung."""
    __tablename__ = "tag"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(unique=True, index=True)


class TagCreate(BaseModel):
    """
    Eingabe-Modell für Tags mit striktem Pattern.
    Nur Kleinbuchstaben, Ziffern und Bindestriche erlaubt.
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = PydanticField(
        min_length=2,
        max_length=30,
        pattern=r"^[a-z0-9-]+$",
        description="Tag-Name: nur Kleinbuchstaben, Ziffern, Bindestriche"
    )


class TagResponse(BaseModel):
    id: int
    name: str


@app.post("/tags", status_code=201)
def create_tag(tag: TagCreate, session: SessionDep) -> TagResponse:
    """Tag mit strikter Validierung erstellen (^[a-z0-9-]+$)."""
    existing = session.exec(select(TagDB).where(TagDB.name == tag.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Tag '{tag.name}' existiert bereits")
    db_tag = TagDB(name=tag.name)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return TagResponse(id=db_tag.id, name=db_tag.name)


# ─────────────────────────────────────────
# Day 4 – Course Datenbank-Modell
# ─────────────────────────────────────────

class CourseDB(SQLModel, table=True):
    """SQLite-Tabelle für Kurse."""
    __tablename__ = "course"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    code: str = SQLField(unique=True, index=True)
    name: str
    semester: int
    ects: int
    lecturer: str


class CourseCreate(BaseModel):
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str


def db_to_course(course: CourseDB) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        code=course.code,
        name=course.name,
        semester=course.semester,
        ects=course.ects,
        lecturer=course.lecturer
    )


# ─────────────────────────────────────────
# Day 4 – Course Endpoints
# ─────────────────────────────────────────

@app.post("/courses", status_code=201)
def create_course(course: CourseCreate, session: SessionDep) -> CourseResponse:
    """Neuen Kurs erstellen. 409 bei doppeltem Code (case-insensitive)."""
    all_courses = session.exec(select(CourseDB)).all()
    for existing in all_courses:
        if existing.code.upper() == course.code.upper():
            raise HTTPException(
                status_code=409,
                detail=f"Course with code '{course.code}' already exists"
            )
    db_course = CourseDB(**course.model_dump())
    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_to_course(db_course)


@app.get("/courses")
def list_courses(
    session: SessionDep,
    semester: Optional[int] = None,
    min_ects: int = 0
) -> list[CourseResponse]:
    """Kurse auflisten mit optionalen Filtern."""
    statement = select(CourseDB)
    if semester is not None:
        statement = statement.where(CourseDB.semester == semester)
    if min_ects > 0:
        statement = statement.where(CourseDB.ects >= min_ects)
    courses = session.exec(statement).all()
    return [db_to_course(c) for c in courses]


@app.get("/courses/{course_id}")
def get_course(course_id: int, session: SessionDep) -> CourseResponse:
    """Einzelnen Kurs per ID abrufen."""
    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(
            status_code=404,
            detail=f"Course with ID {course_id} not found"
        )
    return db_to_course(course)
