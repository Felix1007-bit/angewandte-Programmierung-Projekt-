# Work Log

**Student Name:** Felix

Instructions: Fill out one log for each course day. Content to consider: Course Sessions + Assignment

---

## Week 1

### Day 1

#### 1. ✅ Was habe ich erreicht?

Ich habe meine ersten FastAPI-Endpoints erstellt und die Entwicklungsumgebung eingerichtet (Git, VS Code, uv). Im Kurs haben wir gemeinsam die Klassen-Endpoints /, /status und /about implementiert. Als Hausaufgabe habe ich die drei weiteren Endpoints /square/{number}, /student und /double/{number} selbststaendig fertiggestellt. Dabei habe ich gelernt, wie FastAPI-Routen mit dem @app.get-Decorator definiert werden, wie Pfad-Parameter funktionieren und wie man die automatische Dokumentation unter /docs verwendet.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Ich hatte einen kritischen Fehler: FastAPI wurde zweimal importiert und app wurde zweimal definiert. Das zweite app = FastAPI(...) hat das erste ueberschrieben, wodurch alle Endpoints aus dem ersten Block (/, /status, /about) verloren gegangen sind und in /docs nicht mehr erschienen. Ausserdem fehlten die Klassen-Endpoints /status und /about, die ich vergessen hatte zu implementieren.

---

#### 3. 💡 Wie habe ich sie überwunden?

Ich habe den doppelten Import und die doppelte app-Definition entfernt und alles in einem einzigen zusammenhaengenden Block zusammengefuehrt. Dadurch waren alle Endpoints wieder erreichbar. Ich habe gelernt, dass in FastAPI immer nur eine app-Instanz existieren darf.

---

### Day 2

#### 1. ✅ Was habe ich erreicht?

Ich habe eine vollstaendige Notes-API mit FastAPI und Pydantic aufgebaut. Die Datenmodelle NoteCreate und Note wurden mit BaseModel definiert. Im Kurs haben wir gemeinsam POST /notes (Notiz erstellen), GET /notes (alle Notizen listen) und GET /notes/{id} (einzelne Notiz abrufen) implementiert. Die API speichert Notizen dauerhaft in einer JSON-Datei (data/notes.json) mithilfe der Funktionen load_notes() und save_notes(). Als Hausaufgabe habe ich das category-Feld in die Modelle integriert sowie /notes/stats, /notes/category/{cat} und als Bonus den DELETE-Endpoint hinzugefuegt.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Ich hatte gleich drei Fehler auf einmal: 1. datetime.now(datetime.utc) funktionierte nicht, weil datetime.utc nicht existiert - timezone ist ein separates Objekt, das extra importiert werden muss. 2. Das Feld created_at war als datetime-Objekt typisiert, aber json.dump() kann Python-datetime-Objekte nicht serialisieren. 3. Ich habe note.dict() verwendet, was in Pydantic v2 veraltet ist und zu Fehlern fuehrt.

---

#### 3. 💡 Wie habe ich sie überwunden?

Ich habe timezone aus dem datetime-Modul extra importiert und datetime.now(timezone.utc).isoformat() verwendet. Den Typ von created_at habe ich auf str geaendert, damit der ISO-String direkt gespeichert wird. Ausserdem habe ich note.dict() durch note.model_dump() ersetzt, die korrekte Methode fuer Pydantic v2. Durch diese drei Fixes lief die API stabil.

---

### Day 3

#### 1. ✅ Was habe ich erreicht?

Ich habe die Note-API auf den Stand von Tag 3 gebracht und vollstaendiges CRUD implementiert. Die Modelle NoteCreate und Note wurden um ein tags-Feld (list[str]) erweitert. Der GET /notes Endpoint erhielt Query-Parameter fuer Filterung nach category, search und tag. Neue Endpoints: PUT /notes/{id} zum vollstaendigen Aktualisieren einer Note, PATCH /notes/{id} fuer partielle Updates (nur angegebene Felder werden geaendert), DELETE /notes/{id} mit korrektem Status 204 No Content, GET /tags sowie GET /tags/{tag}/notes als Tag-Ressource, GET /categories und GET /categories/{name}/notes als Kategorien-Ressource. Der Statistik-Endpoint /notes/stats wurde mit top_tags und unique_tags_count erweitert (mithilfe von collections.Counter). Ausserdem wurde ein Datum-Filter (created_after, created_before) in GET /notes integriert. Grundlage waren die Kursunterlagen (day-03-presentation.md) sowie die FastAPI- und Pydantic-Dokumentation.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Es gab mehrere Fehler und fehlende Teile im Code: 1. Das tags-Feld fehlte komplett in NoteCreate und Note - die API konnte keine Tags entgegennehmen oder speichern. 2. GET /notes hatte keine Query-Parameter, Filterung war nicht moeglich. 3. Der PUT-Endpoint fehlte komplett. 4. Der DELETE-Endpoint gab {"message": "Note deleted"} zurueck, anstatt Status 204 No Content ohne Body - das ist nicht RESTful. 5. GET /tags und GET /tags/{tag}/notes fehlten beide komplett. 6. Bei einem neuen /queryparameters-Endpoint fehlte das @-Zeichen vor app.get - der Endpoint wurde daher nicht in der API registriert und erschien nicht in /docs. 7. Im selben Endpoint kam die Pruefung if not param1: return list NACH der for-Schleife. Das verursachte einen TypeError, weil Python None nicht in einem String suchen kann. 8. Hausaufgaben-Tasks 2-5 (erweiterter Stats-Endpoint, /categories-Ressource, PATCH, Datum-Filter) fehlten alle komplett.

---

#### 3. 💡 Wie habe ich sie überwunden?

Den @-Fehler erkannte ich, weil der Endpoint in /docs nicht erschien. Durch genaues Lesen der FastAPI-Dokumentation wurde klar, dass ohne @ der Decorator nicht angewendet wird. Den NoneType-Fehler im Filter behob ich, indem ich die if not param1-Pruefung vor die for-Schleife stellte - so wird bei leerem param1 sofort die volle Liste zurueckgegeben, bevor die Schleife laeuft. Den DELETE-Status korrigierte ich durch Hinzufuegen von status_code=204 im Decorator und einem leeren return (ohne Body), wie es dem REST-Standard entspricht. Das tags-Feld und alle neuen Endpoints (PUT, GET /tags, GET /tags/{tag}/notes) implementierte ich direkt nach dem Muster aus der Kursunterlage day-03-presentation.md. Fuer den PATCH-Endpoint nutzte ich das NoteUpdate-Modell mit Optional-Feldern gemaess Pydantic-Dokumentation (docs.pydantic.dev). Den erweiterten Stats-Endpoint implementierte ich mit collections.Counter, wie in der Aufgabe empfohlen. Die Python-Dokumentation dazu findet sich unter docs.python.org/3/library/collections.html. Alle uebrigen fehlenden Endpoints (/categories, Datum-Filter) wurden anhand der Kursunterlagen (day-03-presentation.md) und der offiziellen FastAPI-Dokumentation (fastapi.tiangolo.com) implementiert.

---

## Week 2

### Day 4

#### 1. ✅ Was habe ich erreicht?

Ich habe die Note-API um ein vollstaendiges Course Catalog API erweitert. Dazu habe ich zwei neue Pydantic-Modelle definiert: CourseCreate (Eingabe, ohne ID) und Course (Ausgabe, mit ID). Nach dem bekannten Muster aus Tag 2 habe ich load_courses() und save_courses() fuer die Datei-Persistenz in courses.json implementiert. Der neue POST /courses Endpoint erstellt Kurse und prueft dabei auf doppelte Kurs-Codes (case-insensitive, Status 409 Conflict bei Duplikat). GET /courses unterstuetzt Filter nach semester und min_ects. Ausserdem habe ich eine umfassende Testsuite (test_notes.py) mit 18 Tests fuer die Notes API geschrieben: CRUD-Tests, Filter-Tests, Fehlerbehandlungs-Tests und Tests fuer alle Day-3-Features. Grundlage: Kursunterlage day-04-presentation.md, pytest-Dokumentation (docs.pytest.org) und FastAPI Testing-Dokumentation.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Ich hatte folgende Fehler und Herausforderungen: 1. In der Kursunterlage steht course.dict() fuer save_courses() und das Erstellen neuer Course-Objekte. Das ist in Pydantic v2 veraltet und wuerde eine DeprecationWarning ausloesen - derselbe Fehler wie schon in Tag 2 bei den Notes. 2. Beim Schreiben der Tests musste ich darauf achten, dass Tests unabhaengig voneinander laufen koennen. Da die API Daten in einer Datei speichert, koennen sich Tests gegenseitig beeinflussen (z.B. wenn ein Test eine Note erstellt und ein anderer Test alle Notes zaehlt). Ich habe das durch eindeutige Testwerte (z.B. uniquetag_abc123) geloest. 3. Der DELETE-Endpoint gibt Status 204 (kein Body) zurueck. response.json() wuerde dabei einen Fehler werfen - der Test darf also nach einem DELETE nicht versuchen die Antwort als JSON zu lesen.

---

#### 3. 💡 Wie habe ich sie überwunden?

Den course.dict()-Fehler habe ich behoben, indem ich direkt course.model_dump() verwendet habe - die korrekte Methode fuer Pydantic v2, wie ich es bereits in Tag 2 gelernt hatte. Das Wissen aus frueheren Fehlern hat hier direkt geholfen. Das Problem mit Test-Isolation habe ich durch eindeutige, zufaellig aussehende Werte in jedem Test geloest (z.B. 'uniquetag_abc123', 'Work_Filter_Test'). So koennen Tests parallel oder in beliebiger Reihenfolge laufen, ohne sich gegenseitig zu stoeren. Den 204-No-Content-Fall habe ich korrekt getestet, indem ich nur response.status_code == 204 pruefe und danach mit einem separaten GET-Request verifiziere, dass die Note wirklich geloescht wurde. Das Arrange-Act-Assert-Muster aus der Kursunterlage hat mir geholfen, Tests klar und lesbar zu strukturieren. Ich habe ausserdem eine Hilfsfunktion create_test_note() geschrieben, um Wiederholungen zu vermeiden.

---

### Day 5

#### 1. ✅ Was habe ich erreicht?

Ich habe Pydantic v2-Validierung in die Notes API eingebaut und die Modelle damit abgesichert. Mit Field(...) habe ich Laengenbeschraenkungen fuer title, content, category und tags gesetzt. Mit field_validator habe ich Normalisierungslogik implementiert: Kategorien werden auf Kleinbuchstaben reduziert, Tags werden getrimmt, dedupliziert und auf Mindestlaenge geprueft. Mit model_validator (mode='after') habe ich eine felduebergreifende Regel umgesetzt: work-Notizen muessen den Tag 'work' enthalten. Ausserdem habe ich ConfigDict(str_strip_whitespace=True, extra='forbid') gesetzt, um automatisch zu trimmen und unbekannte Felder abzulehnen. Zusätzlich habe ich test_validation.py mit 13 Tests für alle Validierungsregeln erstellt.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Ich hatte folgende Fehler und Herausforderungen: 1. Git Push abgelehnt (divergierte Branches): Als ich meinen Code auf GitHub pushen wollte, erschien die Fehlermeldung: 'Your branch and origin/main have diverged'. Mein lokaler Branch war 4 Commits voraus, der Remote-Branch 1 Commit voraus. Git verweigert in diesem Fall den Push, um Datenverlust zu vermeiden. 2. Die bestehenden Tests (test_notes_Felix.py) verwendeten Kategorien wie 'Testing' oder 'Work_Filter_Test', die nach der neuen Validierung nicht mehr erlaubt sind. Alle Testdaten mussten auf gueltige Kategorien (work, personal, school, ideas, general) umgestellt werden. 3. Der model_validator fuer work-Notizen muss nach dem field_validator fuer category laufen, damit self.category bereits normalisiert ist. Das erfordert mode='after'.

---

#### 3. 💡 Wie habe ich sie überwunden?

Zu 1: git pull --rebase origin main ausgefuehrt, um die Remote-Aenderung sauber unter meine Commits zu legen. Danach hat git push origin main ohne Fehler funktioniert. Lerneffekt: --rebase setzt die eigenen Commits auf den Remote-Stand auf, ohne einen Merge-Commit zu erzeugen. Zu 2: test_notes_Felix.py systematisch durchgegangen und alle category-Werte auf erlaubte Kategorien angepasst. work-Notizen benoetigen ausserdem den Pflicht-Tag 'work' (wegen des model_validator). Zu 3: In der Pydantic-Dokumentation nachgelesen, dass mode='after' erst laeuft, wenn alle field_validators abgeschlossen sind. Dadurch ist self.category beim model_validator bereits lowercase.

---

### Day 6

#### 1. ✅ Was habe ich erreicht?

Ich habe klassenbasierte Decorators in Python kennen gelernt und selbst implementiert. In class_based_decorator.py habe ich drei Klassen-Decorators erstellt: @repeat(n) fuehrt eine Funktion n-mal aus, @timer() misst die Ausfuehrungszeit und gibt sie aus, @log_calls() protokolliert jeden Aufruf mit Argumenten und Rueckgabewert. Ich habe gelernt, dass Decorators als Klassen __init__ und __call__ verwenden. Ausserdem habe ich die bestehende Test-Suite (test_notes_Felix.py) an die neuen Validierungsregeln angepasst, damit alle 18 bestehenden Tests weiterhin bestehen. Als Hausaufgabe Tag 6 habe ich die vom Professor bereitgestellte Test-Suite (test_main_professor.py, 70 Tests) heruntergeladen und ausgefuehrt. Beim ersten Durchlauf: 14 bestanden, 17 fehlgeschlagen, 39 Fehler. Nach Analyse aller Fehlermeldungen habe ich drei Bugs in main.py identifiziert und behoben. Danach laufen alle 70 Tests durch.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

Ich hatte folgende Fehler und Herausforderungen: 1. Das Verstaendnis von __init__ vs __call__ bei klassenbasierten Decorators war anfangs unklar. Ich war nicht sicher, wann welche Methode ausgefuehrt wird. 2. Kombinierte Decorators (@log_calls + @timer) laufen in umgekehrter Reihenfolge (von innen nach aussen). Die Ausgabe sah zuerst falsch aus, weil ich die Reihenfolge falsch eingeschaetzt hatte. 3. functools.wraps war mir unbekannt - ohne wraps verliert die dekorierte Funktion ihren Namen und ihren Docstring, was Debugging erschwert. 4. Der model_validator work_notes_need_work_tag blockierte alle Notizen mit category="work" ohne den Tag "work". Da der Professor in seiner Test-Suite ueberall category="work" ohne "work"-Tag verwendet, schlugen alle Fixture-basierten Tests mit 422 fehl statt 201. 5. Die Query-Parameter created_after und created_before waren als str typisiert. Ungueltige Datumswerte wie "not-a-date" oder "2026-13-01" wurden akzeptiert statt mit 422 abgelehnt. 6. Die Tag-Suche GET /tags/{tag_name}/notes war case-sensitive. Eine Anfrage mit "CASE-TAG" fand keine Notizen mit gespeichertem Tag "case-tag".

---

#### 3. 💡 Wie habe ich sie überwunden?

Zu 1: Mit einem einfachen Beispiel nachvollzogen: __init__ laeuft beim @-Aufruf (also einmalig beim Deklarieren), __call__ laeuft bei jedem tatsaechlichen Funktionsaufruf. Zu 2: In der Python-Dokumentation nachgelesen, dass Decorators von unten nach oben angewendet werden. Daher laeuft der innerste Decorator zuerst. Zu 3: functools.wraps hinzugefuegt - es kopiert __name__, __doc__ und weitere Attribute der Originalfunktion auf die wrapper-Funktion, sodass Debugging und Introspection weiterhin korrekt funktionieren. Zu 4: Den model_validator work_notes_need_work_tag vollstaendig entfernt, da er mit der Professor-Test-Suite inkompatibel war. Zu 5: Die Parameter created_after und created_before auf Optional[datetime] umgestellt. FastAPI prueft das Format automatisch und gibt 422 bei ungueltigen Werten zurueck. Zu 6: tag_name.lower() in get_notes_by_tag() hinzugefuegt, sodass die Suche case-insensitive funktioniert.

---

## Week 3

### Day 7

#### 1. ✅ Was habe ich erreicht?

Ich habe Streamlit kennen gelernt und ein vollstaendiges Frontend fuer die Notes-API erstellt (frontend.py). Im Kurs haben wir die Say-No-Test-App implementiert: ein Button ruft eine externe REST-API auf und zeigt die Antwort im UI an. Dabei habe ich st.session_state kennen gelernt, um Werte zwischen Streamlit-Reruns zu persistieren. Als Hausaufgabe habe ich das Streamlit-Frontend mit zwei Tabs implementiert: "Alle Notizen" laedt per GET /notes die gesamte Liste, erlaubt eine Auswahl per Selectbox und zeigt Details an. Zusaetzlich gibt es Filter nach Kategorie und Textsuche. "Neue Notiz erstellen" enthaelt ein st.form-Formular mit Titel, Inhalt, Kategorie und Tags. Beim Absenden wird POST /notes aufgerufen. Validierungsfehler der API (422) werden direkt im UI angezeigt.

---

#### 2. 🚧 Welche Herausforderungen hatte ich?

1. st.session_state war anfangs verwirrend: Streamlit fuehrt das gesamte Skript bei jeder Interaktion neu aus. Ohne session_state geht der Zustand (z.B. Say-No-Text) bei jedem Klick verloren. 2. Wenn der FastAPI-Server nicht laeuft, crasht die Streamlit-App mit einem unbehandelten ConnectionError statt eine nutzbare Fehlermeldung anzuzeigen. 3. st.form mit clear_on_submit: Die Felder sollen nach dem Erstellen einer Notiz automatisch geleert werden. Das korrekte Verhalten musste ich in der Streamlit-Dokumentation nachschlagen.

---

#### 3. 💡 Wie habe ich sie überwunden?

Zu 1: Durch das Kursbeispiel verstanden, dass Streamlit bei jeder Interaktion das Skript komplett neu ausfuehrt. Mit "if key not in st.session_state" wird der Wert nur beim ersten Laden initialisiert und danach persistent gehalten. Zu 2: try/except requests.exceptions.ConnectionError hinzugefuegt. Bei Verbindungsfehler zeigt die App eine st.error-Meldung mit dem Startbefehl ("uv run fastapi dev main.py") an, anstatt zu crashen. Zu 3: In der Streamlit-Dokumentation nachgelesen: st.form(clear_on_submit=True) leert alle Felder nach dem Absenden. Der submit-Button (st.form_submit_button) muss innerhalb des with-Blocks stehen.

---

### Day 8

#### 1. ✅ Was habe ich erreicht?



---

#### 2. 🚧 Welche Herausforderungen hatte ich?



---

#### 3. 💡 Wie habe ich sie überwunden?



---

### Day 9

#### 1. ✅ Was habe ich erreicht?



---

#### 2. 🚧 Welche Herausforderungen hatte ich?



---

#### 3. 💡 Wie habe ich sie überwunden?



---

# 🎉 Congratulations! You did it! 🎓✨
