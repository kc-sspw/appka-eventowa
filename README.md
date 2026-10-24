# Appka eventowa — KC SSPW

Lokalny PoC mobilnego huba wydarzenia z grą fotograficzną. Django 5.2 LTS,
Python 3.13 i PostgreSQL 17; jeden serwer WWW oraz worker kolejki w bazie.
Zakres zatwierdzono 23.10.2026. Prace są na `feat/django-event-poc`, przez draft PR.

## Co działa

- Odizolowane subdomeny, konta uczestników i organizatorów per wydarzenie.
- Grupy, aktualności, stałe informacje i harmonogram z odbiorcami.
- Lokalny import/eksport XLSX: arkusz pozostaje w przeglądarce; API dostaje tylko imię, grupy i dane techniczne konta.
- Losowanie bez powtórek, limit pięciu **niewykonanych** zadań, kompresja zdjęć i podmiana z kontrolą wersji.
- Prywatna galeria, oceny uczestników i organizatorów, komentarze i moderacja.
- Google Drive z OAuth `drive.file`, lokalny FakeStorage, idempotencja i worker odzyskujący operacje po awarii.
- Zamknięcie usuwa dane aplikacji; aktualny album pozostaje u organizatora. Nie ma automatycznego kasowania albumu po 7 ani 30 dniach.

## Uruchomienie od zera

Wymagane: Git, Python 3 do wygenerowania konfiguracji oraz Docker z Compose v2.

```bash
git clone https://github.com/kc-sspw/appka-eventowa.git
cd appka-eventowa
git switch feat/django-event-poc
python3 scripts/init_local.py
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo --participants 12
mkdir -p .private
docker compose cp web:/app/.private/demo-credentials.csv .private/demo-credentials.csv
```

`init_local.py` generuje losowe sekrety do ignorowanego `.env` i nie nadpisuje
istniejącej konfiguracji. `createsuperuser` prosi interaktywnie o login i hasło
administratora platformy; brak publicznego domyślnego hasła.
Seed tworzy dwa aktywne wydarzenia, 50 zadań w każdym, organizatorów i uczestników.
Losowe dostępy są w prywatnym CSV, a nie w logach. Nie uruchamiaj seeda drugi raz
w tej samej bazie. Liczbę uczestników A można ustawić do 500; B ma trzy osoby.

| Adres lokalny | Przeznaczenie |
|---|---|
| http://platform.localhost:8000/admin/ | Administrator platformy |
| http://event-a.events.localhost:8000/ | Wydarzenie A |
| http://event-b.events.localhost:8000/ | Wydarzenie B |

Jeśli system nie rozwiązuje tych nazw, dodaj je do lokalnego pliku hosts jako
`127.0.0.1`. Dla nowego slugu dodaj analogiczny wpis. Cookies są oddzielne dla
hostów; konta eventowe nie logują się do panelu platformy.

Web sam wykonuje migracje i `collectstatic`; worker startuje po gotowości weba.
Zdjęcia testowe, cache i CSV są w prywatnym wolumenie, poza katalogiem static.
`docker compose down` zatrzymuje środowisko, zachowując wolumeny.
Nie dodawaj `--volumes`, jeśli chcesz zachować bazę i lokalny album.

## Testy

Pełne CI uruchamia PostgreSQL 17 i Chromium, bez rzeczywistych kont Google,
sekretów produkcyjnych ani deploymentu. Wyniki i ograniczenia:
[raport weryfikacji](docs/testing.md).

Lokalny runner Python 3.13 i testowa baza PostgreSQL:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d db
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
set -a
. ./.env
set +a
export PGHOST=127.0.0.1
export DJANGO_SETTINGS_MODULE=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q -m 'not browser'
python -m playwright install --with-deps chromium --only-shell
RUN_BROWSER_TESTS=1 pytest -q
ruff check .
ruff format --check .
```

Runner wymaga uprawnienia `CREATEDB` w **lokalnej testowej** bazie. Nigdy nie kieruj
`config.test_settings` do środowiska używanego przez uczestników. Ustawienia testów
stosują szybkie hashowanie wyłącznie dla danych syntetycznych.
Pomocniczy `LOCAL_SQLITE_SMOKE=1 pytest -m 'not browser and not concurrency'` nie
zastępuje PostgreSQL; testy blokad na SQLite są jawnie pomijane.

## Dokumentacja i granice

- [Instrukcja organizatora](docs/organizer-guide.md)
- [Administracja, Drive i utrzymanie](docs/operations.md)
- [Wymagania](docs/requirements.md), [pełna specyfikacja](docs/IMPLEMENTATION_PROMPT.md), [ADR](docs/decisions/README.md)
- [Testy i ograniczenia](docs/testing.md), [gotowość do pilotażu](docs/poc-readiness.md)
- [Referencje i autorstwo](docs/source-provenance.md), [zasady PR](CONTRIBUTING.md), [bezpieczeństwo](SECURITY.md)

Google Drive ma prawdziwy adapter, ale **nie wykonano live OAuth/uploadu** z kontem
organizatora. Lokalny start używa FakeStorage, zabronionego poza DEBUG.
PoC nie jest zatwierdzonym wdrożeniem dla prawdziwych uczestników. Brak rankingu,
push, SMS, rejestracji publicznej i produkcyjnego deploymentu GitHub Actions.
