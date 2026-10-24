# Plan implementacji

Gałąź: `feat/django-event-poc`, od main `2f2fcc0`; jeden zależny draft PR, kolejne logiczne commity.

## 13. Plan implementacji i testy odbioru

Kolejność logicznych PR-ów (lub kolejnych commitów w draft PR, jeśli zależności utrudniają osobne PR-y):

1. Dokumentacja decyzji, Django/PostgreSQL, event resolver, konta/role, dwa eventy i testy izolacji.
2. Pionowy wycinek: organizer → konto → przydział → upload do FakeStorage → galeria → organizer score. Już tutaj atomowość limitu i prywatny download.
3. Import/eksport XLSX, grupy, aktualności, stałe informacje i harmonogram.
4. Prawdziwy Drive, OAuth, idempotencja, podmiana, moderacja, retry i limity miejsca.
5. Komentarze/oceny uczestników, pełne zamknięcie, instrukcje oraz całościowa weryfikacja.

Minimum testów automatycznych:

- A/B: uczestnik i organizator A nie odczytują ani nie zapisują obiektów B przez zmianę URL, body, group ID, assignment ID, photo ID, callback state lub job payload. Test również miniatur, eksportu/importu i cache.
- Sesja nie daje uprawnień na obcym hoście; uczestnik nie zmienia roli, eventu i właściciela. Nieznany host, nieznany slug i closed event nie ujawniają danych.
- XLSX: kilka identycznych imion, fikcyjny PESEL/mail, grupy, zachowane wartości; spy na sieć dowodzi braku zbędnych komórek. Retry tworzy jeden zestaw kont. Utrata wyniku/reset są udokumentowane.
- Treści: ALL + kilka grup, brak grup, ukryta zakładka, dodanie STATIC podczas eventu, plan sortowany po dniach. Próba XSS pozostaje tekstem.
- Gra: czas przed/w trakcie/po, brak puli, wyczerpanie, brak ponownego zadania, rozkład najmniej przydzielonych, limit 5, wycofanie zadania. Dwa równoczesne draw przy 4 aktywnych dają najwyżej 5; ponowienie tego samego requestu nie losuje drugiego.
- Upload: poprawny/niepoprawny MIME, zbyt duży obraz, limit pikseli, usunięte EXIF/GPS, orientacja, limit końcowy. Timeout Drive przed/po zapisie, pełny dysk, cofnięta zgoda, restart workera i błąd DB po uploadzie nie tworzą fałszywego sukcesu lub niekontrolowanych duplikatów.
- Podmiana: błąd zachowuje stare zdjęcie; sukces usuwa stare oceny/komentarze i planuje usunięcie starego pliku. Konkurencyjna podmiana nie gubi nowszego zdjęcia. Moderacja i zamknięcie wygrywają z uploadem bez późniejszego odtworzenia pliku w galerii.
- Oceny 1–5/0–5, brak samooceny uczestnika, jedna ocena na osobę, edycja nie zwiększa liczby głosów. Komentarze i usuwanie przestrzegają ról.
- Budżet miejsca: dwie równoczesne rezerwacje nie przekraczają limitu; pending delete nadal liczy się do zużycia do potwierdzenia usunięcia.
- Close A: odcięcie sesji, czyszczenie danych/cache/tokenów, zachowanie archiwum i istniejącego albumu, B nadal działa. Retry czyszczenia jest idempotentne, pending cloud failure nie daje fałszywego CLOSED.

Współbieżność testuj na PostgreSQL, nie traktuj SQLite jako dowodu działania blokad. Testy przeglądarkowe: mobilne 360–430 px i desktop, klawiatura/focus/etykiety, loading/error/success, brak poziomego overflow; przynajmniej pełny scenariusz dwóch uczestników i organizatora. Generuj obrazy testowe, nie kopiuj zdjęć z referencji.

Definition of done: instrukcja uruchomienia od zera, migracje, seed dwóch wydarzeń z kontami wygenerowanymi lokalnie (bez publicznego stałego hasła admina), komplet MUST, testy z wynikiem, brak sekretów/danych w Git, dokumentacja reuse, instrukcja organizatora i raport ograniczeń. Przykładowy zestaw syntetyczny może mieć 200 kont i 50 zadań w A oraz kilka kont w B; nie jest to gwarancja wydajności dla 200 jednoczesnych uploadów. Zmierz podstawowy scenariusz i opisz środowisko, bez deklarowania nieprzetestowanego SLA.


## Stan wykonania — 24.10.2026

Wszystkie pięć etapów implementacji znajduje się w draft PR #6 na
`feat/django-event-poc`: moduły Django, migracje, seed, UI, lokalny parser XLSX,
adaptery magazynu, worker i testy. Dokumentacja: README, instrukcja organizatora,
operacje/Google OAuth oraz raport testów. Pełny run PostgreSQL + Chromium już
przeszedł; końcowe wyniki przypięte są w [testing.md](testing.md).
Live Drive i warunki prawdziwego pilotażu pozostają osobnymi krokami.
