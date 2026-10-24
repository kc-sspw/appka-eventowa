# Weryfikacja PoC — 24.10.2026

## Wykonane sprawdzenia

Pełny run [GitHub Actions 40099533875](https://github.com/kc-sspw/appka-eventowa/actions/runs/40099533875)
dla `b7fd20fce82e79817b6167af744a433018dcc972`: **74 passed**, bez ostrzeżeń,
w 12,57 s. Środowisko: Ubuntu GitHub-hosted runner, Python 3.13.16, PostgreSQL
17.11, Chromium 156 przez Playwright 1.64.1, FakeStorage i dane syntetyczne.
Obejmuje sześć testów prawdziwej współbieżności i dwa scenariusze przeglądarkowe,
w tym rzeczywisty ponowny import wyeksportowanego XLSX.

Lint, formatowanie, `manage.py check`, brak brakujących migracji i migracja
pustej bazy przeszły. Lokalnie: **66 passed, 8 deselected** (SQLite, bez testów
współbieżności i przeglądarki). Lokalny wynik nie stanowi dowodu działania blokad;
te sprawdzono na PostgreSQL w CI. Linki lokalne Markdown i `git diff --check`
nie wykazały błędów.

## Start od zera w Docker Compose

[Run 40099761986](https://github.com/kc-sspw/appka-eventowa/actions/runs/40099761986)
dla `768563eb174ac5984f895e8b6f266ea66901817a` sprawdził również instrukcję startu:
generowanie losowego `.env`, budowę obrazu, start web/db/worker z healthcheck,
migracje, `collectstatic`, seed dwóch eventów, HTTP 200 obu hostów oraz zamknięcie
A przez worker przy zachowaniu kont B. Kontenery i wolumeny były jednorazowe.
Nie jest to deployment i nie używa danych lub kont produkcyjnych.

## Pokryte scenariusze

| Obszar | Sprawdzenia |
|---|---|
| Izolacja i role | Obce hosty/UUID, uczestnik vs organizer/platforma, prywatny download i miniatury, obce grupy, payload roli/eventu, reset sesji, CSRF, limit loginu |
| Import | Atomowość, retry identycznego batcha, konflikt payloadu, reimport własnych loginów, allowlista pól; XLSX z arkuszem zaczynającym się w B2, jednakowe imiona, zera wiodące, długie identyfikatory, tekst wyglądający jak formuła, kilka arkuszy |
| Prywatność XLSX | Spy żądań sieciowych w Chromium dowodzi, że dodatkowe komórki nie opuszczają przeglądarki; brak localStorage i zewnętrznych żądań |
| Treści | Filtrowanie grup, ukryta zakładka Informacje, przyszła publikacja, kolejność planu, tekst XSS pozostaje tekstem |
| Gra | Czas gry, pusta/wyczerpana pula, brak powtórek, najmniej użyte zadania, limit pięciu, wycofanie, niezmienność treści po przydziale |
| Zdjęcia | Format/MIME, rozmiar/piksele, animacja, EXIF/orientacja, idempotencja, timeout przed/po zapisie, pełny dysk, cofnięta zgoda, awaria DB po zapisie |
| Podmiana/moderacja | Stare zdjęcie do sukcesu nowego, czyszczenie ocen/komentarzy, oczekujące usunięcie liczone do budżetu, przegrana wersja, brak odtworzenia po moderacji/close |
| Drive/OAuth | MockTransport prawdziwego adaptera: prealokowane ID, brak duplikatu po timeout, obcy folder/event/operacja, 404 delete, quota, refresh i szyfrowanie; state/session/event/expiry/replay |
| Zamknięcie | Minimalne archiwum, zachowanie aktualnego albumu, odcięcie A bez uszkodzenia B, retry, niewyzerowane pending delete, in-flight upload |
| PostgreSQL | Cztery draw przy czterech aktywnych; ten sam request/import równolegle; dwie rezerwacje budżetu; dwie finalizacje podmiany; moderacja vs rezerwacja; close vs finalizacja |
| Chromium | Dwie sesje uczestników i organizator: login → draw → upload → ocena/komentarz → moderacja → close; eksport XLSX; szerokości 360/390/430/1280, overflow i focus |

Zrzuty z CI (`synthetic-test-results`) zostały obejrzane: mobilna gra, desktopowy
szczegół zdjęcia i import mają czytelne formularze i nawigację. Test czeka na
załadowanie miniatur i sprawdza ich rzeczywistą szerokość. Czerwony prostokąt
na zdjęciu to generowany obraz testowy, nie materiał uczestnika.

Dodatkowe testy końcowe obejmują dziennik admina i tymczasowe pliki per event,
platformowy limit prób, utworzenie lokalnego magazynu, zduplikowaną grupę,
stabilną liczbę zapytań galerii oraz odmowę ponownego otwarcia przez stary formularz.

## Pomiar podstawowego scenariusza

`test_capacity.py` tworzy 200 kont i 50 zadań, wykonuje 200 **kolejnych** losowań,
24 uploady generowanego JPEG 80×60 i renderuje HTML galerii. Wyniki środowiska
zapisuje w `test-results/capacity.json`, dołączanym do artefaktów CI.
Używa szybkiego testowego hashera MD5 i FakeStorage. Pomiar nie obejmuje
produkcyjnego hashowania, Drive, sieci, dużych zdjęć ani 200 równoczesnych uploadów.
Nie jest SLA lub testem wydajności docelowej infrastruktury.

Wynik PostgreSQL z powyższego runu:

| Etap sekwencyjny | Czas |
|---|---:|
| Utworzenie 200 kont (testowy hasher) | 0,524 s |
| 200 losowań z puli 50 zadań | 0,794 s |
| 24 małe obrazy do FakeStorage | 0,246 s |
| Render HTML galerii 24 zdjęć | 0,018 s |

Osobny test porównuje liczbę zapytań przy jednym i 24 zdjęciach: nie rośnie
z każdym zdjęciem. Te wartości opisują tylko wskazane środowisko i dane.

## Nieprzetestowane i ograniczenia

- Brak live OAuth, rzeczywistego Drive, limitów Google i testu docelowego konta organizatora.
- Brak rzeczywistych urządzeń iOS/Android, Safari oraz sieci wyjazdowej.
- Brak pełnego audytu bezpieczeństwa i niezależnego review; testy nie dowodzą braku wszystkich podatności.
- Brak wdrożenia, weryfikacji DNS/TLS/proxy, backup/restore i retencji logów infrastruktury.
- PoC serializuje mutacje w obrębie eventu; nie deklaruje wydajności przy dużym ruchu.
- Import obsługuje standardowe XLSX, nie makra/szyfrowanie/zaawansowane style. Po utracie karty niezapisane hasła wymagają resetu.
- Automatyczne operacje chmurowe są odzyskiwane po dzierżawie/backoff. Ręczne potwierdzenie usunięcia wymaga niezależnej weryfikacji operatora.

Warunki użycia prawdziwych danych: [poc-readiness.md](poc-readiness.md).
