# ADR-006 — zamkniecie

Status: zaakceptowane do lokalnego PoC (23.10.2026).

## 10. Zamknięcie — ADR-006

Event: DRAFT → ACTIVE → CLOSING → CLOSED. Ustawiona data końca lub ręczna akcja organizatora inicjuje CLOSING. Zamknięcie jest nieodwracalne w PoC; osobny ekran potwierdzenia pokazuje skutki i folder, który należy zachować. Termin końca eventu jest osobny od końca gry, aby można było jeszcze obejrzeć/ocenić zdjęcia.

Wejście w CLOSING natychmiast blokuje uczestników i nowe operacje gry; panel organizatora ma wyłącznie stan porządkowania. Każdy request dodatkowo sprawdza ends_at, więc opóźnienie workera nie przedłuża dostępu. Trwające uploady nie mogą opublikować nowych zdjęć po rozpoczęciu zamknięcia. Worker kończy lub anuluje operacje, usuwa osierocone i już wskazane do usunięcia pliki. Nie usuwa aktualnego albumu.

Po rozliczeniu operacji usuwa konta uczestników i organizatorów danego eventu, grupy, wpisy, harmonogram, pulę/przydziały, komentarze/oceny, referencje plików, importy, sesje, tokeny, cache, tymczasowe pliki i dzienniki eventowe. Konta platformowe zostają. Jeśli błąd Google uniemożliwia sprzątnięcie pending delete, usuń zbędną treść, pozostaw tylko minimum operacji/folder/token potrzebne do retry i status cleanup_failed w CLOSING; nie oznaczaj CLOSED. Platform admin może ponowić lub po ręcznej weryfikacji usunięcia w chmurze zakończyć sprzątanie. Nie przetrzymuj całej bazy eventu dla jednego błędu plikowego.

Archiwum CLOSED: UUID, zarezerwowany slug, nazwa eventu, daty początku/końca, status, cleaned_at. Bez album URL, nazwisk, kont, liczb głosów, zdjęć i tokenów. Dane do diagnozy wyłącznie ogólne, bez payloadów i nazw plików użytkownika. Logi techniczne maks. 7 dni jako domyślne założenie; przed pilotem sprawdzić także reverse proxy. Lokalny PoC nie tworzy backupów. Dla wdrożenia proponujemy szyfrowane backupy z maks. 7-dniowym cyklem i procedurą ponownego czyszczenia CLOSED po restore przed udostępnieniem systemu; nie deklarować tego jako wdrożonego bez konfiguracji infrastruktury.

Usunięcie lokalnych tokenów nie jest równoznaczne z cofnięciem zgody całej aplikacji Google. Nie wykonuj bezmyślnie globalnego revoke mogącego zakłócić inne eventy tego konta; zapewnij instrukcję ręcznego odłączenia po zakończeniu wszystkich takich eventów.

Folder pozostaje własnością organizatora. Po zamknięciu moderacja i usunięcie albumu odbywają się w Google Drive. Siedem dni to propozycja organizacyjna dla albumu, nie timer aplikacji i nie automatyczna reguła Google. Dawna propozycja „aplikacja kasuje zdjęcia po 30 dniach” nie obowiązuje.

