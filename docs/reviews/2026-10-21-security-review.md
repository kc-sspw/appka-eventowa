# Przegląd referencji i warunków bezpieczeństwa — 2026-10-21

**Status:** przegląd statyczny / draft, nie certyfikat bezpieczeństwa, brak wdrożenia. 
**Repo produktu:** `kc-sspw/appka-eventowa` (prywatne; w `main` tylko dokumentacja).
**Źródła:** `kc-sspw/apka-wyjazdowa` (Poligon, publiczne), `Korniszon99/SSPWPhotoTaskGame` (publiczne), `Korniszon99/PWGame` (publiczne), `kc-sspw/.github`, `kc-sspw/handbook`.
**Stan źródeł:** odczyt z domyślnych gałęzi 2026-10-21. Nie znaleziono `AGENTS.md` ani `CODEOWNERS` w odczytanych drzewach default branch. Nie wyklucza to innych refów lub ustawień repo.

## Ustalenia według ważności

**P0 — krytyczne przed kopiowaniem / PoC z uczestnikami:**

| ID | Dowód (plik:linia w repo źródłowym) | Co ustalono i dlaczego jest ważne | Warunek zamknięcia |
|---|---|---|---|
| P0-1 | `apka-wyjazdowa/src/main/java/me/havooc/poligon/security/SecurityConfig.java:28-32`; `.../controller/CrewController.java:26-34`; `.../model/Crew.java:22-34` | GET `/**` jest publiczny, `GET /api/crew` zwraca bezpośrednio encję zawierającą m.in. e-mail, telefon, pokój, rolę, flagę administratora i inne informacje. `findVisibleCrews` wyklucza tylko rekordy ukryte, nie pola osobowe (`.../repository/CrewRepository.java:18-19`). Nie dowodzi to, że istnieje aktywna, publicznie dostępna instancja. | Po stronie przyszłego produktu: kontrola dostępu do każdego zasobu, projekcje DTO i jawny katalog dopuszczonych publicznych pól. Bez testu negatywnego nie wdrażać. |
| P0-2 | `apka-wyjazdowa/src/main/java/me/havooc/poligon/security/WebSocketConfig.java:19-23`; `.../security/WebSocketHandler.java:21-22,29-46,54-57`; `.../controller/CrewController.java:39-40` | Handshake WebSocket dopuszcza wszystkie originy, kod rejestruje połączenia bez kontroli członkostwa wydarzenia, a broadcast przekazuje pełny payload wszystkim sesjom. Poważne ryzyko ujawnienia danych pomiędzy niezależnymi wyjazdami. | Nowy model kanałów/tematów scoped do eventu, weryfikacja sesji i uprawnień, testy cross-event denial; nie kopiować globalnego broadcastera. |
| P0-3 | `apka-wyjazdowa/src/main/java/me/havooc/poligon/security/FirebaseAuthenticationFilter.java:33-46`; `.../controller/CrewController.java:36-59,96-100`; `.../model/Crew.java:33` | Token Firebase i lista dozwolonych e-maili służą do **uwierzytelniania**, ale filtr tworzy sesję z pustą listą uprawnień; endpointy zapisu/usunięcia nie weryfikują ról, a przy update możliwa jest zmiana `isSuperAdmin`. Użytkownik dozwolony w systemie może mieć nadmierny zakres działań; wymaga testu w środowisku izolowanym. | Macierz ról i operacji, autoryzacja serwerowa per event i rola, zakaz przyjmowania flag uprzywilejowania z niezaufanego żądania; test odmowy. |
| P0-4 | `SSPWPhotoTaskGame/photo_game/database/schema.sql:2-36`; `appka-eventowa/docs/requirements.md:11-19` | Model zdjęć/zadań/użytkowników/ratingów jest globalny: nie ma `event_id`. Nie spełnia wymogu odrębnych, równoległych wydarzeń. To luka modelu, nie potwierdzony wyciek działającej aplikacji. | Model `event_id` i izolacja każdego odczytu, zapisu, uprawnienia, uploadu, kolejki i retencji. Test A nie widzi danych wydarzenia B. |
| P0-5 | `apka-wyjazdowa/docker-compose.yml:34-40`; `.../compose/app/Dockerfile:1-7`; `.../service/VerifiedUsersService.java:20-26,95-101` | W zastanej wersji repo znajdował się jawny literal hasła PostgreSQL, Dockerfile wykonywał `COPY .env .` (ryzyko umieszczenia sekretów w warstwie build), a logi drukowały e-maile i listę osób uprawnionych. | Zmiany sanitarne tylko w draft PR. Ustalić, czy hasło i inne poświadczenia były kiedykolwiek używane; jeśli tak: natychmiast unieważnić/obrócić i ocenić ekspozycję obrazów, build-cache oraz logów. Sama zmiana pliku NIE usuwa ryzyka historycznego. |
| P0-6 | `PWGame/README.md:43-50,87-91`; `SSPWPhotoTaskGame/SECURITY.md:3-15` | Starszy PWGame opisuje domyślne konto administracyjne i kod dostępu. Nowszy projekt deklaruje usunięcie domyślnych poświadczeń/debug endpointu, ale wskazuje na konieczność rotacji w już wdrożonych instancjach. | Nie kopiować bootstrappingu ani danych startowych starej wersji. Właściciel weryfikuje i w razie potrzeby rotuje rzeczywiście używane poświadczenia i kody. |
| P0-7 | `apka-wyjazdowa/src/main/java/me/havooc/poligon/model/Crew.java:1-3`; `.../controller/CrewController.java:1-3`; brak rozpoznanej licencji w metadanych wszystkich trzech repo referencyjnych | Autorstwo w Poligonie jest wskazane w nagłówkach, ale licencja/prawa do ponownego wykorzystania kodu nie są potwierdzone. Publiczna widoczność nie oznacza zgody na kopiowanie do nowego produktu. | Ustalić właścicieli praw i zakres pisemnej zgody, zachować autorstwo. Do tego czasu implementować wymagane zachowanie niezależnie, bez kopiowania plików. |

**P1 — wysokie / wymagają kontroli przed wdrożeniem:**

| ID | Dowód | Ustalenie i działanie |
|---|---|---|
| P1-1 | `SSPWPhotoTaskGame/photo_game/sw.js:36-65` | Strategia cache-first obejmuje wszystkie obrazy JPG/PNG itp. bez rozróżnienia uploadów; zdjęcia uczestników mogły trafiać do Cache Storage. Przygotowano odrębny draft PR ograniczający cache do jawnej listy statycznych assetów; potrzebny test w przeglądarce, usunięcie starych cache i niezależna polityka retencji danych. |
| P1-2 | `SSPWPhotoTaskGame/.github/workflows/main_sspwphototaskgame.yml:4-10,39-75` | `push` do `main` uruchamia Azure Production deployment; `workflow_dispatch` także umożliwia ręczne uruchomienie. Żadnego push/merge do `main` w ramach tego audytu. Właściciel musi zweryfikować reguły środowiska Production i wymagane approval. |
| P1-3 | `SSPWPhotoTaskGame/.github/workflows/ci.yml:6-17`, `security.yml:6-23`, `main_sspwphototaskgame.yml:12-73` | CI i skaner deklarują `permissions: contents: read`, deploy używa w osobnym jobie `id-token: write` i `contents: read`. Dobra praktyka minimalnego zakresu w plikach, ale Actions używają ruchomych tagów `@vN`, nie pełnych SHA. Przed użyciem w produkcie wymagany przegląd provenance, pinning i ustawień organizacji. Skaner `gitleaks dir` skanuje bieżące pliki, nie dowodzi czystości historii. |
| P1-4 | `apka-wyjazdowa/src/main/java/me/havooc/poligon/security/CorsConfig.java:18-34`; `.../resources/application.properties:8-9` | Wzorca CORS `https://*.azurewebsites.net` i credentials=true nie traktować jako decyzji dla produktu. `ddl-auto=update` i `show-sql=true` nie mogą przejść bez osobnego przeglądu bezpieczeństwa danych i migracji DB. |
| P1-5 | `SSPWPhotoTaskGame/photo_game/config/config.php:3-11,42-44`; `.../auth/register.php:13-14,52-67` | Są pewne zabezpieczenia (cookies sesyjne, CSRF przy rejestracji, hash haseł); nie należy przedstawiać całej gry jako pozbawionej zabezpieczeń. Nie przeprowadzono jednak pełnego audytu autoryzacji każdego endpointu ani testów runtime. |

**P2 — porządki i zależności:**

| ID | Dowód | Ustalenie |
|---|---|---|
| P2-1 | `apka-wyjazdowa/pom.xml:5-8,29-45`; `flutter/pubspec.yaml:20-45`; drzewo repo | Maven deklaruje wersje i korzysta z BOM; Flutter ma `pubspec.yaml`, ale w odczytanym drzewie nie ma `pubspec.lock`. Bez kontrolowanego resolve/dependency audit i aktualnego lockfile nie oceniono podatności transitive dependencies. |
| P2-2 | Drzewo `SSPWPhotoTaskGame`: brak `composer.json`/`composer.lock` i `package-lock.json` | To PHP/SQLite bez tych manifestów. Brak lockfile sam w sobie nie dowodzi podatności. Trzeba ustalić rzeczywiste zależności runtime PHP/serwera i zabezpieczenia hostingu. |
| P2-3 | `appka-eventowa/README.md:40-52`; `handbook/docs/projects.md:25-53`; `.github/CONTRIBUTING.md:9-16,67-73` | Projekt docelowy jest jeszcze dokumentacyjny. Standard KC wymaga review ważniejszych zmian i oddziela szkolenia od repo utrzymywanych. Nie ma obecnie wykonywalnych testów ani workflowów w repo produktu. |

## Kontrole techniczne rzeczywiście wykonane

- Odczyt drzew i metadanych repo, wskazanych plików oraz historii; domyślne gałęzie repo `appka-eventowa`, `apka-wyjazdowa`, `SSPWPhotoTaskGame` i `PWGame` odczytano jako `protected: false`. W `appka-eventowa` API rulesets odpowiedziało 403 (komunikat o planie), a odczyt branch protection 403 (`Resource not accessible by integration`). To **nie** jest pełny odczyt wszystkich ustawień ochrony.
- Metadane źródeł nie wykazały licencji; w odczytanych drzewach nie ma `CODEOWNERS` ani `AGENTS.md`.
- W repo produktu nie ma kodu aplikacyjnego ani Actions; istnieją tylko README, wymagania, szablony Issue/PR i CONTRIBUTING.
- W SSPWPhotoTaskGame są trzy workflowy. `ci.yml` sprawdza PHP 8.3 i bootstrap; `security.yml` skanuje bieżący katalog; osobny workflow wdraża do Azure po push do `main` lub manual dispatch. Nie uruchomiono go.
- Heurystycznie przejrzano aktualne wrażliwe pliki Poligonu, PhotoTaskGame i wybrane diffy Git historii (w tym 28 commitów zwróconych przez wyszukiwanie PhotoTaskGame oraz commity dostępne w PWGame/Poligonie). Nie wykazano kompletnego, certyfikowanego skanu wszystkich obiektów i refów. W Poligonie zidentyfikowano literal hasła bazy i logowanie PII; w historii starszej gry istnieją przykładowe dane startowe.
- Brak potwierdzenia uruchomienia rzeczywistych testów serwera, Flutter, Docker, bazy, przeglądarki, skanowania CVE, GitHub Secret Scanning, audit log, 2FA, ról zespołów i polityki workflowów z forków.

## Decyzje i działania właściciela organizacji / repozytoriów (UI)

1. **Organizacja `kc-sspw`:** Settings → Member privileges → Base permissions: brak szerokiego Write; Repository creation: jeśli szkolenie się zakończyło, wyłączyć możliwość tworzenia repo przez wszystkich zwykłych Members. Forking repo prywatnych i creation to oddzielne przełączniki. Sprawdzić Teams i direct/outside collaborators.
2. **Org People / Security:** sprawdzić 2–3 Owners, 2FA, osoby z admin/maintain i konta po szkoleniu. Audit log (jeśli dostępny): przebieg zmian repo i dostępów.
3. **Repo `appka-eventowa`:** Settings → Collaborators and teams: minimalny dostęp; Settings → Rules / Branches: sprawdzić możliwość review wymagającego 1 akceptacji, blokadę force-push i usuwania `main`, stale branch PR, required checks gdy faktycznie istnieją. Jeżeli plan nie pozwala wymusić ochrony prywatnego repo, utrzymać repo prywatne i stosować manualny review; **nie podnosić planu ani nie upubliczniać repo bez decyzji**.
4. **Repo `appka-eventowa` / `SSPWPhotoTaskGame`:** Settings → Actions → General: ustalić allowed actions, zasadę pinowania SHA, read-only default token, wymagania zatwierdzania PR/workflowów z forków, zakaz udostępniania sekretów nieufnym workflowom. Rozważyć CODEOWNERS dopiero po potwierdzeniu rzeczywistych zespołów i uprawnień; plik sam nie wymusza review.
5. **Repo `SSPWPhotoTaskGame`:** Settings → Environments → Production: potwierdzić protected branches, required reviewers i przypisanie poświadczeń tylko do środowiska. Nie uruchamiać `workflow_dispatch`.
6. **Sekrety/historyczne konta:** prywatnie potwierdzić, czy literal PostgreSQL z Poligonu lub bootstrap PWGame był użyty poza izolowanym demo. Wtedy unieważnić/obrócić odpowiednie poświadczenia i skontrolować logi, obrazy, archiwa i wdrożenia. Bez wartości sekretów w Issues.
7. **Prawa do kodu:** skontaktować się z rzeczywistymi autorami/właścicielami trzech referencji i zapisać pozwolenie na ponowne użycie; brak licencji nie oznacza domeny publicznej.

## Warunek rozpoczęcia PoC

PoC można rozpocząć **dopiero gdy**: (a) właściciel potwierdził prawa do materiałów lub wybrano niezależną implementację bez kopiowania; (b) nie ma aktywnych znanych, ujawnionych poświadczeń, a historyczne użycie/rotacja zostały ocenione; (c) zatwierdzono minimalną specyfikację z izolacją per event, autoryzacją serwerową i minimalizacją danych; (d) zdefiniowano politykę zdjęć, retencji i cache; (e) wyznaczono opiekuna review i bezpieczną ścieżkę testów bez automatycznego wdrożenia produkcyjnego.

Pierwszy PoC ma używać **danych syntetycznych i izolowanego środowiska**, bez prawdziwych danych uczestników. Zakres minimalny to informacje/komunikaty, zadania i zdjęcia typu BeReal oraz obsługa wielu niezależnych wydarzeń, zgodnie z wcześniejszymi uzgodnieniami; push nie jest warunkiem PoC. Konkretne zachowania wymagają zatwierdzenia w `docs/requirements.md`.

**Nie stwierdzono gotowości produkcyjnej żadnej z referencji.**
