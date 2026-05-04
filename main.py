from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
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

class NoteCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: list[str] = []  # Day 3: Tags-Feld hinzugefügt

class Note(BaseModel):
    id: int
    title: str
    content: str
    category: str
    tags: list[str] = []  # Day 3: Tags-Feld hinzugefügt
    created_at: str

# Day 3 Hausaufgabe Task 4: Modell für PATCH (nur optionale Felder)
class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None

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
    created_after: str = None,   # Day 3 Hausaufgabe Task 5
    created_before: str = None   # Day 3 Hausaufgabe Task 5
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
        # Filter by category
        if category and note.category != category:
            continue

        # Filter by search term (Titel und Inhalt)
        if search:
            search_lower = search.lower()
            title_match = search_lower in note.title.lower()
            content_match = search_lower in note.content.lower()
            if not (title_match or content_match):
                continue

        # Filter by tag
        if tag and tag not in note.tags:
            continue

        # Day 3 Hausaufgabe Task 5: Datum-Filter
        if created_after and note.created_at < created_after:
            continue

        if created_before and note.created_at > created_before:
            continue

        filtered.append(note)

    return filtered


# WICHTIG: /notes/stats muss VOR /notes/{note_id} definiert sein!
@app.get("/notes/stats")
def get_notes_stats():
    """
    Get statistics about notes.
    Day 3 Hausaufgabe Task 2: Erweitert mit top_tags und unique_tags_count
    """
    notes_db, _ = load_notes()

    categories = {}
    for note in notes_db:
        if note.category in categories:
            categories[note.category] += 1
        else:
            categories[note.category] = 1

    # Alle Tags zählen mit Counter (Day 3 Hausaufgabe Task 2)
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


# Day 3: PUT Endpoint zum Aktualisieren einer Note
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
                created_at=note.created_at  # Erstellungsdatum bleibt erhalten
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
    """
    Partially update a note (only provided fields are updated).
    Unlike PUT, PATCH only updates fields you provide.
    """
    notes_db, _ = load_notes()

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            # Nur die übergebenen Felder aktualisieren
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


# Day 3: DELETE mit Status 204 (No Content)
@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    """Delete a note by ID. Returns 204 No Content on success."""
    notes_db, _ = load_notes()

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            notes_db.pop(i)
            save_notes(notes_db)
            return  # 204 = kein Response-Body

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
        for tag in note.tags:
            all_tags.add(tag)

    return sorted(list(all_tags))


@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str) -> list[Note]:
    """Get all notes with a specific tag"""
    notes_db, _ = load_notes()

    filtered = [note for note in notes_db if tag_name in note.tags]
    return filtered


# ─────────────────────────────────────────
# Day 3 Hausaufgabe Task 3 – Categories Endpoints
# ─────────────────────────────────────────

@app.get("/categories")
def list_categories() -> list[str]:
    """Get all unique categories from all notes"""
    notes_db, _ = load_notes()

    categories = set(note.category for note in notes_db)
    return sorted(list(categories))


@app.get("/categories/{category_name}/notes")
def get_notes_by_category(category_name: str) -> list[Note]:
    """Get all notes in a specific category"""
    notes_db, _ = load_notes()

    filtered = [note for note in notes_db if note.category == category_name]
    return filtered


# ─────────────────────────────────────────
# Day 3 – Query Parameters (Übung)
# ─────────────────────────────────────────

@app.get("/queryparameters")
def query_parameters(param1: str = None, param2: int = None) -> dict:
    namen = ["Alice", "Bob", "Charlie"]

    if not param1:
        return {"namen": namen}

    name_gefiltert = []
    for name in namen:
        if param1 in name:
            name_gefiltert.append(name)

    return {
        "param1": param1,
        "param2": param2,
        "namen": name_gefiltert
    }
