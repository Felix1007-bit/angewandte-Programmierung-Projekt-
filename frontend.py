""""
- Streamlit Installieren
- Streamlit App "Hello, World!" erstellen und testen
- "Say no" - App als ersten Test erstellen
  - API Documentation: https://github.com/hotheadhacker/no-as-a-service
  - API Endpoint: https://naas.isalman.dev/no
  - Button in Streamlit, der bei Klick eine Anfrage an den API Endpoint sendet und die Antwort anzeigt

- Todos für Nachmittag:
  - Streamlit App mit 2 Funktionen von Notizen API
  - Funktion 1: Alle Notizen anzeigen
    - Liste von Titeln von Notizen anzeigen
    - Möglichkeit zu einem Titel den Inhalt, Tags, Category, etc. anzuzeigen
  - Funktion 2: Neue Notiz erstellen (Formular mit Titel und Inhalt, Button)
    - Erstellen einer neuen Notiz (Titel, Inhalt, Tags, Category)
    - Neu erstellte Notiz soll in Liste auftauchen
"""
 
import streamlit as st
import pandas as pd
 
st.write("Hello *world!*")