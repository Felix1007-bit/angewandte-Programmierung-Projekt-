from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime, timezone
from typing import Optional, Self
from collections import Counter
import json
from pathlib import Path

app = FastAPI(
    title="Angewandte Programmierung",
    description="Simple note management API",
    version="1.0.0"
)

# ─────────────────────────────────────────
# Day 1 – Klassen-Endpoints
# ─────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Hello World!"}

@app.get("/status")
def get_status():
    return {
        "status": "online",
        "version": "0.1.0",
        "day": 1
    }

@app.get("/about")
def get_about():
    return {
        "project": "My First API",
        "author": "Felix",
        "course": "Applied Programming"
    }

# ─────────────────────────────────────────
# Day 1 – Hausaufgaben-Endpoints
# ─────────────────────────────────────────

@app.get("/square/{number}")
def calculate_square(number: int):
    result = number * number
    return {
        "number": number,
        "square": result,
        "calculation": f"{number} × {number} = {result}"
    }

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
    return {
        "number": number,
        "double": result,
        "calculation": f"{number} × 2 = {result}"
    }

# ─────────────────────────────────────────
# Day 2/3 – Note Taking API – Datenmodelle
# ─────────────────────────────────────────

# Erlaubte Kategorien (Day 5)
ALLOWED_CATEGORIES = {"work", "personal", "school", "ideas", "general"}


class NoteCreate(BaseModel):
    # Day 5: ConfigDict – automatisch trimmen + keine Extra-Felder
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    title: str = Field(
        min_length=3,
        max_length=100,
        description="Kurzer Notiztitel (3–100 Zeichen)",
        examples=["Einkaufsliste", "Meeting-Vorbereitung"]
    )
    content: str = Field(
        min_length=1,
        max_length=10_000,
        description="Inhalt der Notiz (1–10.000 Zeichen)"
    )
    category: str = Field(
        min_length=2,
        max_length=30,
        description=f"Kategorie – erlaubt: {sorted(ALLOWED_CATEGORIES)}",
        examples=["work"]
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Bis zu 10 Tags (werden kleingeschrieben & dedupliziert)"
    )

    # Day 5 Task 1: Titel darf nicht nur Leerzeichen sein
    @field_validator("title")
    @classmethod
    def title_not_only_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Titel darf nicht nur aus Leerzeichen bestehen")
        return value

    # Day 5 Task 2: Kategorie normalisieren + auf Whitelist prüfen
    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"category muss eines von {sorted(ALLOWED_CATEGORIES)} sein"
            )
        return normalized

    # Day 5 Task 2: Tags bereinigen – strip, lowercase, Duplikate entfernen
    @field_validator("tags")
    @classmethod
    def clean_tags(cls, raw: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for tag in raw:
            t = tag.strip().lower()
            if not t:
                raise ValueError("Tags dürfen keine leeren Zeichenketten sein")
            if len(t) < 2:
                raise ValueError(f"Tag '{t}' muss mindestens 2 Zeichen haben")
            if t in seen:
                continue  # Duplikat – still entfernen
            seen.add(t)
            cleaned.append(t)
        return cleaned

    # Day 5 Task 3: Cross-Field-Regel – work-Notizen brauchen Tag "work"
    @model_validator(mode="after")
    def work_notes_need_work_tag(self) -> Self:
        # Warum model_validator: Diese Regel verbindet zwei Felder (category + tags),
        # deshalb kann kein field_validator allein entscheiden.
        if self.category == "work" and "work" not in self.tags:
            raise ValueError(
                "work-Notizen müssen den Tag 'work' in der Tag-Liste enthalten"
            )
        return self


class Note(BaseModel):
    id: int
    title: str
    content: str
    category: str
    tags: list[str] = []
    created_at: str


# Day 3 Hausaufgabe Task 4 + Day 5 Task 4: PATCH – optionale Felder mit Constraints
class NoteUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10_000)
    category: Optional[str] = Field(default=None, min_length=2, max_length=30)
    tags: Optional[list[str]] = Field(default=None, max_length=10)

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"category muss eines von {sorted(ALLOWED_CATEGORIES)} sein"
            )
        return normalized

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, raw: Optional[list[str]]) -> Optional[list[str]]:
        if raw is None:
            return raw
        cleaned: list[str] = []
        seen: set[str] = set()
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


# ─────────────────────────────────────────
# Day 2 – Datei-Persistenz
# ─────────────────────────────────────────

NOTES_FILE = Path("data/notes.json")

def load_notes():
    """Load notes from JSON file and return notes list and next ID counter"""
    notes_db = []
    note_id_counter = 1

    if NOTES_FILE.exists():
        with open(NOTES_FILE, 'r') as f:
            data = json.load(f)
            notes_db = [Note(**note) for note in data]

            if notes_db:
                note_id_counter = max(note.id for note in notes_db) + 1

    return notes_db, note_id_counter


def save_notes(notes_db):
    """Save notes to JSON file after each change"""
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(NOTES_FILE, 'w') as f:
        notes_data = [note.model_dump() for note in notes_db]
        json.dump(notes_data, f, indent=2)

# ─────────────────────────────────────────
# Day 2/3 – Notes Endpoints
# ─────────────────────────────────────────

@app.post("/notes", status_code=201)
def create_note(note: NoteCreate) -> Note:
    """Create a new note"""
    notes_db, note_id_counter = load_notes()

    new_note = Note(
        id=note_id_counter,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=note.tags,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    notes_db.append(new_note)
    save_notes(notes_db)

    return new_note


# Day 3: GET /notes mit Query-Parametern für Filterung
@app.get("/notes")
def list_notes(
    category: str = None,
    search: str = None,
    tag: str = None,
    created_after: str = None,
    created_before: str = None
) -> list[Note]:
    """
    List notes with optional filters:
    - category: Filter by category
    - search: Search in title and content
    - tag: Filter by tag
    - created_after: Only notes created after this date (ISO format)
    - created_before: Only notes created before this date (ISO format)
    """
    notes_db, _ = load_notes()

    filtered = []
    for note in notes_db:
        if category and note.category != category:
            continue
        if search:
            search_lower = search.lower()
            if not (search_lower in note.title.lower() or search_lower in note.content.lower()):
                continue
        if tag and tag not in note.tags:
            continue
        if created_after and note.created_at < created_after:
            continue
        if created_before and note.created_at > created_before:
            continue
        filtered.append(note)

    return filtered


# WICHTIG: /notes/stats muss VOR /notes/{note_id} definiert sein!
@app.get("/notes/stats")
def get_notes_stats():
    """Get statistics about notes."""
    notes_db, _ = load_notes()

    categories = {}
    for note in notes_db:
        categories[note.category] = categories.get(note.category, 0) + 1

    all_tags = []
    for note in notes_db:
        all_tags.extend(note.tags)

    tag_counter = Counter(all_tags)
    top_tags = [
        {"tag": tag, "count": count}
        for tag, count in tag_counter.most_common(5)
    ]

    return {
        "total_notes": len(notes_db),
        "by_category": categories,
        "top_tags": top_tags,
        "unique_tags_count": len(tag_counter)
    }


@app.get("/notes/{note_id}")
def get_note(note_id: int) -> Note:
    """Get a specific note by ID"""
    notes_db, _ = load_notes()

    for note in notes_db:
        if note.id == note_id:
            return note

    raise HTTPException(
        status_code=404,
        detail=f"Note with ID {note_id} not found"
    )


@app.put("/notes/{note_id}")
def update_note(note_id: int, note_update: NoteCreate) -> Note:
    """Update an existing note (replaces all fields)"""
    notes_db, _ = load_notes()

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            updated_note = Note(
                id=note.id,
                title=note_update.title,
                content=note_update.content,
                category=note_update.category,
                tags=note_update.tags,
                created_at=note.created_at
            )
            notes_db[i] = updated_note
            save_notes(notes_db)
            return updated_note

    raise HTTPException(
        status_code=404,
        detail=f"Note with ID {note_id} not found"
    )


# Day 3 Hausaufgabe Task 4: PATCH Endpoint für partielle Updates
@app.patch("/notes/{note_id}")
def partial_update_note(note_id: int, note_update: NoteUpdate) -> Note:
    """Partially update a note (only provided fields are updated)."""
    notes_db, _ = load_notes()

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            if note_update.title is not None:
                note.title = note_update.title
            if note_update.content is not None:
                note.content = note_update.content
            if note_update.category is not None:
                note.category = note_update.category
            if note_update.tags is not None:
                note.tags = note_update.tags

            notes_db[i] = note
            save_notes(notes_db)
            return note

    raise HTTPException(status_code=404, detail="Note not found")


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    """Delete a note by ID. Returns 204 No Content on success."""
    notes_db, _ = load_notes()

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            notes_db.pop(i)
            save_notes(notes_db)
            return

    raise HTTPException(404, "Note not found")


# ─────────────────────────────────────────
# Day 3 – Tags Endpoints
# ─────────────────────────────────────────

@app.get("/tags")
def list_tags() -> list[str]:
    """Get all unique tags from all notes"""
    notes_db, _ = load_notes()
    all_tags = set()
    for note in notes_db:
        all_tags.update(note.tags)
    return sorted(list(all_tags))


@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str) -> list[Note]:
    """Get all notes with a specific tag"""
    notes_db, _ = load_notes()
    return [note for note in notes_db if tag_name in note.tags]


# ─────────────────────────────────────────
# Day 3 Hausaufgabe Task 3 – Categories Endpoints
# ─────────────────────────────────────────

@app.get("/categories")
def list_categories() -> list[str]:
    """Get all unique categories from all notes"""
    notes_db, _ = load_notes()
    return sorted(list(set(note.category for note in notes_db)))


@app.get("/categories/{category_name}/notes")
def get_notes_by_category(category_name: str) -> list[Note]:
    """Get all notes in a specific category"""
    notes_db, _ = load_notes()
    return [note for note in notes_db if note.category == category_name]


# ─────────────────────────────────────────
# Day 3 – Query Parameters (Übung)
# ─────────────────────────────────────────

@app.get("/queryparameters")
def query_parameters(param1: str = None, param2: int = None) -> dict:
    namen = ["Alice", "Bob", "Charlie"]

    if not param1:
        return {"namen": namen}

    name_gefiltert = [name for name in namen if param1 in name]

    return {
        "param1": param1,
        "param2": param2,
        "namen": name_gefiltert
    }

# ─────────────────────────────────────────
# Day 4 – Course Catalog API – Datenmodelle
# ─────────────────────────────────────────

class CourseCreate(BaseModel):
    """Model for creating courses (no ID)"""
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str


class Course(BaseModel):
    """Model for courses (with ID)"""
    id: int
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str

# ─────────────────────────────────────────
# Day 4 – Course Datei-Persistenz
# ─────────────────────────────────────────

COURSES_FILE = Path("courses.json")


def load_courses():
    """Load courses from JSON file and return courses list and next ID counter"""
    courses_db = []
    course_id_counter = 1

    if COURSES_FILE.exists():
        with open(COURSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            courses_db = [Course(**course) for course in data]

            if courses_db:
                course_id_counter = max(c.id for c in courses_db) + 1

    return courses_db, course_id_counter


def save_courses(courses_db):
    """Save courses to JSON file after each change"""
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        courses_data = [course.model_dump() for course in courses_db]
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────
# Day 4 – Course Endpoints
# ─────────────────────────────────────────

@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> Course:
    """Create a new course. Returns 409 if course code already exists."""
    courses_db, course_id_counter = load_courses()

    for existing in courses_db:
        if existing.code.upper() == course.code.upper():
            raise HTTPException(
                status_code=409,
                detail=f"Course with code '{course.code}' already exists"
            )

    new_course = Course(
        id=course_id_counter,
        **course.model_dump()
    )

    courses_db.append(new_course)
    save_courses(courses_db)

    return new_course


@app.get("/courses")
def list_courses(semester: int = None, min_ects: int = 0) -> list[Course]:
    """List all courses with optional filters"""
    courses_db, _ = load_courses()

    filtered = courses_db

    if semester is not None:
        filtered = [c for c in filtered if c.semester == semester]

    if min_ects > 0:
        filtered = [c for c in filtered if c.ects >= min_ects]

    return filtered


@app.get("/courses/{course_id}")
def get_course(course_id: int) -> Course:
    """Get a specific course by ID"""
    courses_db, _ = load_courses()

    for course in courses_db:
        if course.id == course_id:
            return course

    raise HTTPException(
        status_code=404,
        detail=f"Course with ID {course_id} not found"
    )
