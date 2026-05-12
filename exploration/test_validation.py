"""
Day 5 Hausaufgabe – test_validation.py
Tests für Pydantic-Validierung in der Notes API
"""
import requests

BASE_URL = "http://127.0.0.1:8000"


def valid_note(**overrides):
    """Gibt ein gültiges Note-Dict zurück, einzelne Felder können überschrieben werden."""
    base = {
        "title": "Gültige Testnote",
        "content": "Gültiger Inhalt",
        "category": "personal",
        "tags": ["validtag"]
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────
# Task 1: Field-Constraints
# ─────────────────────────────────────────

def test_create_note_rejects_short_title():
    """Titel mit weniger als 3 Zeichen → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(title="ab"))
    assert response.status_code == 422, f"Erwartet 422, bekam {response.status_code}"


def test_create_note_rejects_empty_title():
    """Leerer Titel → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(title=""))
    assert response.status_code == 422


def test_create_note_rejects_whitespace_title():
    """Titel der nur aus Leerzeichen besteht → 422 (field_validator)"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(title="   "))
    assert response.status_code == 422


def test_create_note_rejects_empty_content():
    """Leerer content → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(content=""))
    assert response.status_code == 422


def test_create_note_rejects_too_many_tags():
    """Mehr als 10 Tags → 422"""
    too_many = [f"tag{i:02d}" for i in range(11)]
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(tags=too_many))
    assert response.status_code == 422


# ─────────────────────────────────────────
# Task 2: Category-Validator
# ─────────────────────────────────────────

def test_create_note_rejects_unknown_category():
    """Unbekannte Kategorie → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(category="ungueltig"))
    assert response.status_code == 422, f"Erwartet 422, bekam {response.status_code}"


def test_create_note_normalizes_category_to_lowercase():
    """Kategorie wird vor dem Speichern zu Kleinbuchstaben normalisiert"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(category="WORK", tags=["work"]))
    assert response.status_code == 201
    assert response.json()["category"] == "work"


# ─────────────────────────────────────────
# Task 2: Tag-Validator
# ─────────────────────────────────────────

def test_create_note_normalizes_tags():
    """Tags werden trimmed und zu Kleinbuchstaben normalisiert, Duplikate entfernt"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(
        category="personal",
        tags=["URGENT", "urgent", "  meeting  ", "Q2"]
    ))
    assert response.status_code == 201
    tags = response.json()["tags"]
    assert "urgent" in tags
    assert "meeting" in tags
    assert "q2" in tags
    # Duplikat darf nur einmal vorkommen
    assert tags.count("urgent") == 1


def test_create_note_rejects_empty_tag():
    """Leerer Tag → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(tags=["", "ok-tag"]))
    assert response.status_code == 422


def test_create_note_rejects_short_tag():
    """Tag mit weniger als 2 Zeichen → 422"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(tags=["x"]))
    assert response.status_code == 422


# ─────────────────────────────────────────
# Task 2: extra="forbid"
# ─────────────────────────────────────────

def test_create_note_forbids_extra_fields():
    """Unbekannte Felder im Request-Body → 422 (extra='forbid')"""
    data = valid_note()
    data["tagz"] = ["tippfehler"]  # extra field
    response = requests.post(f"{BASE_URL}/notes", json=data)
    assert response.status_code == 422


# ─────────────────────────────────────────
# Task 3: work-Notizen (category="work" ist erlaubt, kein Pflicht-Tag)
# ─────────────────────────────────────────

def test_work_note_succeeds_without_work_tag():
    """work-Notiz ohne Tag 'work' → 201 (kein cross-field Validator im Professor-Code)"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(
        category="work",
        tags=["meeting", "projekt"]
    ))
    assert response.status_code == 201


def test_work_note_succeeds_with_work_tag():
    """work-Notiz mit Tag 'work' → 201"""
    response = requests.post(f"{BASE_URL}/notes", json=valid_note(
        category="work",
        tags=["work", "meeting"]
    ))
    assert response.status_code == 201


# ─────────────────────────────────────────
# Task 5/6: Tag-Endpoint Validierung
# ─────────────────────────────────────────

def test_tag_name_rejects_uppercase():
    """POST /tags mit Großbuchstaben → 422 (pattern ^[a-z0-9-]+$)"""
    response = requests.post(f"{BASE_URL}/tags", json={"name": "UPPERCASE"})
    assert response.status_code == 422, f"Erwartet 422, bekam {response.status_code}"


def test_tag_name_accepts_valid():
    """POST /tags mit gültigem Namen → 201 (oder 409 wenn Tag bereits existiert)"""
    response = requests.post(f"{BASE_URL}/tags", json={"name": "valid-tag-01"})
    assert response.status_code in (201, 409), f"Erwartet 201 oder 409, bekam {response.status_code}"


def test_tag_name_rejects_spaces():
    """POST /tags mit Leerzeichen → 422"""
    response = requests.post(f"{BASE_URL}/tags", json={"name": "no spaces"})
    assert response.status_code == 422


def test_tag_name_rejects_too_short():
    """POST /tags mit weniger als 2 Zeichen → 422"""
    response = requests.post(f"{BASE_URL}/tags", json={"name": "x"})
    assert response.status_code == 422


# ─────────────────────────────────────────
# Task 4: NoteUpdate (PATCH) – Constraints bleiben erhalten
# ─────────────────────────────────────────

def test_patch_with_empty_body_succeeds():
    """PATCH mit leerem Body {} → 200 (alle Felder bleiben unverändert)"""
    create_resp = requests.post(f"{BASE_URL}/notes", json=valid_note(title="Patch Basis Note"))
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    response = requests.patch(f"{BASE_URL}/notes/{note_id}", json={})
    assert response.status_code == 200


def test_patch_with_invalid_title_fails():
    """PATCH mit ungültigem Titel → 422"""
    create_resp = requests.post(f"{BASE_URL}/notes", json=valid_note(title="Patch Validation Note"))
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    response = requests.patch(f"{BASE_URL}/notes/{note_id}", json={"title": "ab"})
    assert response.status_code == 422


def test_patch_with_invalid_category_fails():
    """PATCH mit ungültiger Kategorie → 422"""
    create_resp = requests.post(f"{BASE_URL}/notes", json=valid_note(title="Patch Cat Note"))
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    response = requests.patch(f"{BASE_URL}/notes/{note_id}", json={"category": "ungueltig"})
    assert response.status_code == 422


# ─────────────────────────────────────────
# Direkt ausfuehren (ohne pytest)
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    tests = [
        ("Field Constraints", [
            test_create_note_rejects_short_title,
            test_create_note_rejects_empty_title,
            test_create_note_rejects_whitespace_title,
            test_create_note_rejects_empty_content,
            test_create_note_rejects_too_many_tags,
        ]),
        ("Category Validator", [
            test_create_note_rejects_unknown_category,
            test_create_note_normalizes_category_to_lowercase,
        ]),
        ("Tag Validator", [
            test_create_note_normalizes_tags,
            test_create_note_rejects_empty_tag,
            test_create_note_rejects_short_tag,
        ]),
        ("Extra Fields Verboten", [
            test_create_note_forbids_extra_fields,
        ]),
        ("Work-Notizen", [
            test_work_note_succeeds_without_work_tag,
            test_work_note_succeeds_with_work_tag,
        ]),
        ("Tag-Endpoint Validierung", [
            test_tag_name_rejects_uppercase,
            test_tag_name_accepts_valid,
            test_tag_name_rejects_spaces,
            test_tag_name_rejects_too_short,
        ]),
        ("PATCH Validation", [
            test_patch_with_empty_body_succeeds,
            test_patch_with_invalid_title_fails,
            test_patch_with_invalid_category_fails,
        ]),
    ]

    passed = 0
    failed = 0

    for group, group_tests in tests:
        print(f"\n{'='*50}")
        print(f"  {group}")
        print(f"{'='*50}")
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

    print(f"\n{'='*50}")
    print(f"  {passed} bestanden  |  {failed} fehlgeschlagen")
    print(f"{'='*50}\n")
    sys.exit(0 if failed == 0 else 1)
