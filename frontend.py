"""
Day 7 Hausaufgabe – Streamlit Frontend für die Notes API

Starten:
  Terminal 1: uv run fastapi dev main.py
  Terminal 2: uv run streamlit run frontend.py
"""

import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"
CATEGORIES = ["work", "personal", "school", "ideas", "general"]

# ─────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────

def load_notes() -> list[dict]:
    """Alle Notizen von der API laden."""
    try:
        response = requests.get(f"{API_BASE}/notes", timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        pass
    return None  # None = Verbindungsfehler


def create_note(title: str, content: str, category: str, tags: list[str]) -> tuple[int, dict]:
    """Neue Notiz erstellen. Gibt (status_code, response_json) zurück."""
    payload = {
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
    }
    try:
        response = requests.post(f"{API_BASE}/notes", json=payload, timeout=3)
        return response.status_code, response.json()
    except requests.exceptions.ConnectionError:
        return 0, {}


# ─────────────────────────────────────────
# Seitenaufbau
# ─────────────────────────────────────────

st.set_page_config(page_title="Notes App", page_icon="📝", layout="wide")
st.title("📝 Notes App")
st.caption("Streamlit-Frontend für die FastAPI Notes-API")

# ─────────────────────────────────────────
# Say-No Test-App (Kursbeispiel)
# ─────────────────────────────────────────

with st.expander("🙅 Say-No Test-App (Kursbeispiel)"):
    NO_URL = "https://naas.isalman.dev/no"

    def request_no() -> str:
        try:
            r = requests.get(NO_URL, timeout=5)
            return r.json().get("reason", "No.")
        except Exception:
            return "Nein."

    if "say_no_text" not in st.session_state:
        st.session_state["say_no_text"] = request_no()

    name = st.text_input("Name", placeholder="Hier Name eingeben...")
    if name:
        st.write(f"Hallo, {name}!")

    if st.button("Neue Absage generieren"):
        st.session_state["say_no_text"] = request_no()

    st.info(st.session_state["say_no_text"])

    with st.expander("Session State"):
        st.write(st.session_state)

st.divider()

# ─────────────────────────────────────────
# Hauptnavigation per Tabs
# ─────────────────────────────────────────

tab1, tab2 = st.tabs(["📋 Alle Notizen", "➕ Neue Notiz erstellen"])


# ══════════════════════════════════════════
# Tab 1 – Alle Notizen anzeigen
# ══════════════════════════════════════════

with tab1:
    st.subheader("Alle Notizen")

    notes = load_notes()

    if notes is None:
        st.error(
            "⚠️ Verbindung zur API fehlgeschlagen.\n"
            "Bitte FastAPI-Server starten: `uv run fastapi dev main.py`"
        )
    elif len(notes) == 0:
        st.info("Noch keine Notizen vorhanden. Erstelle deine erste Notiz im Tab ➕.")
    else:
        # Filter-Optionen
        with st.expander("🔍 Filter"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_category = st.selectbox(
                    "Kategorie", ["Alle"] + CATEGORIES, key="filter_cat"
                )
            with col_f2:
                filter_search = st.text_input("Suche (Titel / Inhalt)", key="filter_search")

        # Gefilterte Liste
        filtered = notes
        if filter_category != "Alle":
            filtered = [n for n in filtered if n["category"] == filter_category]
        if filter_search:
            q = filter_search.lower()
            filtered = [
                n for n in filtered
                if q in n["title"].lower() or q in n["content"].lower()
            ]

        st.write(f"**{len(filtered)} Notiz(en)** gefunden")

        if not filtered:
            st.warning("Keine Notizen passen zu den gewählten Filtern.")
        else:
            # Titelauswahl
            options = {f"[{n['id']}] {n['title']} ({n['category']})": n for n in filtered}
            selected_label = st.selectbox("Notiz auswählen:", list(options.keys()))
            note = options[selected_label]

            # Detailansicht
            st.subheader(note["title"])
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(note["content"])
            with col2:
                st.write(f"**ID:** `{note['id']}`")
                st.write(f"**Kategorie:** `{note['category']}`")
                tags_str = ", ".join(f"`{t}`" for t in note["tags"]) if note["tags"] else "—"
                st.write(f"**Tags:** {tags_str}")
                st.write(f"**Erstellt:** {note['created_at'][:10]}")


# ══════════════════════════════════════════
# Tab 2 – Neue Notiz erstellen
# ══════════════════════════════════════════

with tab2:
    st.subheader("Neue Notiz erstellen")

    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("Titel *", placeholder="z.B. Einkaufsliste")
        content = st.text_area("Inhalt *", placeholder="Was möchtest du notieren?", height=150)
        category = st.selectbox("Kategorie *", CATEGORIES)
        tags_input = st.text_input(
            "Tags (kommagetrennt)",
            placeholder="z.B. urgent, meeting, projekt",
        )
        submitted = st.form_submit_button("✅ Notiz erstellen", type="primary")

    if submitted:
        tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]

        if not title.strip():
            st.error("Titel darf nicht leer sein.")
        elif not content.strip():
            st.error("Inhalt darf nicht leer sein.")
        else:
            status, body = create_note(title.strip(), content.strip(), category, tags)

            if status == 0:
                st.error(
                    "⚠️ Verbindung zur API fehlgeschlagen.\n"
                    "Bitte FastAPI-Server starten: `uv run fastapi dev main.py`"
                )
            elif status == 201:
                st.success(f"✅ Notiz '{body['title']}' erstellt! (ID: {body['id']})")
                st.json(body)
            elif status == 422:
                for err in body.get("detail", []):
                    field = " → ".join(str(x) for x in err.get("loc", []))
                    st.error(f"Validierungsfehler ({field}): {err.get('msg', str(err))}")
            else:
                st.error(f"Fehler {status}: {body}")
