import requests

BASE_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────
# Hilfsfunktion: Note erstellen
# ─────────────────────────────────────────

def create_test_note(title="Test Note", content="Test Inhalt", category="Testing", tags=None):
    """Erstellt eine Test-Note und gibt die Response zurück"""
    if tags is None:
        tags = ["test", "pytest"]
    return requests.post(f"{BASE_URL}/notes", json={
        "title": title,
        "content": content,
        "category": category,
        "tags": tags
    })

# ─────────────────────────────────────────
# Task 1: CRUD Tests
# ─────────────────────────────────────────

def test_create_note():
    """Test: Neue Note erstellen"""
    # Arrange
    note_data = {
        "title": "Test Note",
        "content": "Test Inhalt",
        "category": "Testing",
        "tags": ["test", "pytest"]
    }
    # Act
    response = requests.post(f"{BASE_URL}/notes", json=note_data)
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["category"] == "Testing"
    assert "id" in data
    assert "created_at" in data
    assert "pytest" in data["tags"]


def test_list_notes():
    """Test: Alle Notes auflisten"""
    response = requests.get(f"{BASE_URL}/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_note_by_id():
    """Test: Einzelne Note per ID abrufen"""
    create_resp = create_test_note(title="Note fuer ID-Test")
    note_id = create_resp.json()["id"]
    response = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id
    assert response.json()["title"] == "Note fuer ID-Test"


def test_update_note():
    """Test: Note vollstaendig aktualisieren (PUT)"""
    create_resp = create_test_note(title="Original Titel")
    note_id = create_resp.json()["id"]
    updated_data = {
        "title": "Aktualisierter Titel",
        "content": "Neuer Inhalt",
        "category": "Updated",
        "tags": ["updated"]
    }
    response = requests.put(f"{BASE_URL}/notes/{note_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Aktualisierter Titel"
    assert data["category"] == "Updated"
    assert data["created_at"] == create_resp.json()["created_at"]


def test_delete_note():
    """Test: Note loeschen und verifizieren dass sie weg ist"""
    create_resp = create_test_note(title="Note zum Loeschen")
    note_id = create_resp.json()["id"]
    response = requests.delete(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 204
    get_resp = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert get_resp.status_code == 404

# ─────────────────────────────────────────
# Task 2: Filter Tests
# ─────────────────────────────────────────

def test_filter_by_category():
    """Test: Notes nach Kategorie filtern"""
    create_test_note(title="Work Note", category="Work_Filter_Test")
    response = requests.get(f"{BASE_URL}/notes?category=Work_Filter_Test")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 1
    for note in notes:
        assert note["category"] == "Work_Filter_Test"


def test_filter_by_search():
    """Test: Notes nach Suchbegriff filtern"""
    create_test_note(title="Suchbegriff_XYZ789 im Titel", content="Normaler Inhalt")
    response = requests.get(f"{BASE_URL}/notes?search=Suchbegriff_XYZ789")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 1
    for note in notes:
        found = "suchbegriff_xyz789" in note["title"].lower() or \
                "suchbegriff_xyz789" in note["content"].lower()
        assert found


def test_filter_by_tag():
    """Test: Notes nach Tag filtern"""
    create_test_note(title="Tagged Note", tags=["uniquetag_abc123"])
    response = requests.get(f"{BASE_URL}/notes?tag=uniquetag_abc123")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 1
    for note in notes:
        assert "uniquetag_abc123" in note["tags"]


def test_combined_filters():
    """Test: Mehrere Filter gleichzeitig anwenden"""
    create_test_note(
        title="Kombination Meeting Note",
        content="Inhalt",
        category="CombinedTest",
        tags=["kombi_tag"]
    )
    response = requests.get(
        f"{BASE_URL}/notes?category=CombinedTest&tag=kombi_tag&search=Kombination"
    )
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 1

# ─────────────────────────────────────────
# Task 3: Fehlerbehandlung Tests
# ─────────────────────────────────────────

def test_create_note_missing_field():
    """Test: Note mit fehlendem Pflichtfeld → 422"""
    invalid_data = {"title": "Nur Titel"}
    response = requests.post(f"{BASE_URL}/notes", json=invalid_data)
    assert response.status_code == 422


def test_get_nonexistent_note():
    """Test: Nicht-existente Note → 404"""
    response = requests.get(f"{BASE_URL}/notes/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_nonexistent_note():
    """Test: Nicht-existente Note aktualisieren → 404"""
    response = requests.put(f"{BASE_URL}/notes/99999", json={
        "title": "x", "content": "x", "category": "x", "tags": []
    })
    assert response.status_code == 404


def test_delete_nonexistent_note():
    """Test: Nicht-existente Note loeschen → 404"""
    response = requests.delete(f"{BASE_URL}/notes/99999")
    assert response.status_code == 404

# ─────────────────────────────────────────
# Task 4: Day 3 Features Tests
# ─────────────────────────────────────────

def test_notes_statistics():
    """Test: GET /notes/stats gibt korrekte Statistiken zurueck"""
    create_test_note()
    response = requests.get(f"{BASE_URL}/notes/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_notes" in data
    assert "by_category" in data
    assert "top_tags" in data
    assert "unique_tags_count" in data
    assert data["total_notes"] >= 1


def test_patch_note():
    """Test: PATCH aktualisiert nur angegebene Felder"""
    create_resp = create_test_note(title="Original", content="Unveraenderter Inhalt")
    note_id = create_resp.json()["id"]
    response = requests.patch(f"{BASE_URL}/notes/{note_id}", json={"title": "Nur Titel geaendert"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Nur Titel geaendert"
    assert data["content"] == "Unveraenderter Inhalt"

# ─────────────────────────────────────────
# Bonus: Tags und Categories
# ─────────────────────────────────────────

def test_list_tags():
    """Test: GET /tags gibt Liste aller Tags zurueck"""
    create_test_note(tags=["bonus_tag_xyz"])
    response = requests.get(f"{BASE_URL}/tags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "bonus_tag_xyz" in response.json()


def test_get_notes_by_tag_resource():
    """Test: GET /tags/{tag}/notes gibt korrekte Notes zurueck"""
    create_test_note(title="Tag Resource Test", tags=["resource_tag_abc"])
    response = requests.get(f"{BASE_URL}/tags/resource_tag_abc/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 1
    for note in notes:
        assert "resource_tag_abc" in note["tags"]


def test_list_categories():
    """Test: GET /categories gibt sortierte Kategorien zurueck"""
    create_test_note(category="KategorieXYZ")
    response = requests.get(f"{BASE_URL}/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "KategorieXYZ" in categories


# ─────────────────────────────────────────
# Direkt ausfuehren (ohne pytest)
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    tests = [
        ("CRUD", [test_create_note, test_list_notes, test_get_note_by_id,
                  test_update_note, test_delete_note]),
        ("Filter", [test_filter_by_category, test_filter_by_search,
                    test_filter_by_tag, test_combined_filters]),
        ("Fehlerbehandlung", [test_create_note_missing_field, test_get_nonexistent_note,
                              test_update_nonexistent_note, test_delete_nonexistent_note]),
        ("Day 3 Features", [test_notes_statistics, test_patch_note]),
        ("Bonus: Tags & Categories", [test_list_tags, test_get_notes_by_tag_resource,
                                      test_list_categories]),
    ]

    passed = 0
    failed = 0

    for group, group_tests in tests:
        print(f"\n========== {group} ==========")
        for test_fn in group_tests:
            try:
                test_fn()
                print(f"  ✅ {test_fn.__name__}")
                passed += 1
            except AssertionError as e:
                print(f"  ❌ {test_fn.__name__} — {e}")
                failed += 1
            except Exception as e:
                print(f"  💥 {test_fn.__name__} — {type(e).__name__}: {e}")
                failed += 1

    print(f"\n========== {passed} bestanden, {failed} fehlgeschlagen ==========\n")
    sys.exit(0 if failed == 0 else 1)
