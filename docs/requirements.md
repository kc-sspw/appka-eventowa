# Zatwierdzony zakres PoC — 23.10.2026

Źródło: specyfikacja właściciela; pełny kontrakt w [IMPLEMENTATION_PROMPT.md](IMPLEMENTATION_PROMPT.md). Zastępuje otwarte decyzje z poprzedniego etapu oraz propozycję 30 dni retencji.

## 2. Potwierdzone wymagania właściciela

- Produkt jest mobilnym hubem informacyjnym wydarzenia z grą fotograficzną.
- Jedna aplikacja obsługuje od początku wiele odizolowanych wydarzeń pod osobnymi subdomenami. Pierwszy realny pilot będzie jeden; test izolacji dwóch wydarzeń należy do PoC.
- Administrator platformy tworzy wydarzenie i przekazuje administrację organizatorom. Organizator zarządza wyłącznie swoim wydarzeniem.
- Konta uczestników są per wydarzenie, tworzone ręcznie lub z eksportu Excel z Forms. Organizator sam przekazuje loginy i hasła, np. mailem.
- Import zwraca dane wejściowe z dwiema dodatkowymi kolumnami login i hasło. PESEL, e-mail i pozostałe zbędne dane nie mają być przechowywane przez aplikację. Przechowujemy maksymalnie imię jako opis osoby oraz niezbędne dane techniczne.
- Uczestnik może należeć do kilku grup. Treści mają odbiorców: wszyscy albo wybrane grupy.
- Aktualności działają niezależnie. Stałe informacje i opcjonalny plan ramowy znajdują się w zakładce Informacje, pojawiającej się dopiero, gdy odbiorca ma dostępną treść.
- Harmonogram tworzy organizator prostym formularzem na stronie. Import Word/PDF/Excel harmonogramu nie jest potrzebny.
- Gra rusza w terminie organizatora, pokazuje instrukcję i umożliwia losowanie z puli. Limit: 5 niezrealizowanych zadań jednocześnie, nie 5 zdjęć na cały wyjazd.
- Jedno aktualne zdjęcie na przydzielone zadanie, z możliwością podmiany przed końcem gry. Gra indywidualna; uczestnicy mogą wykonywać zadania razem poza modelem aplikacji.
- Wspólna galeria wydarzenia, własne zadania/zdjęcia, komentarze, oddzielne oceny organizatorów i uczestników, moderacja. Bez rankingu.
- Pierwszy magazyn zdjęć: Google Drive organizatora. Po wydarzeniu zewnętrzny album pozostaje pod jego opieką i jest udostępniany poza aplikacją.
- Zamknięcie odbiera dostęp pod subdomeną i usuwa dane operacyjne aplikacji. Archiwum ma być minimalne.

## 3. Zakres i priorytety

| Priorytet | Elementy | Warunek odbioru |
|---|---|---|
| MUST | Eventy, role, logowanie, konta, grupy, import lokalny i eksport dostępów | Organizator przygotowuje dwa wydarzenia bez ujawniania danych między nimi |
| MUST | Aktualności, stałe informacje, harmonogram z odbiorcami | Dwa konta z różnych grup widzą właściwe treści i zakładki |
| MUST | Instrukcja/start gry, pula, losowanie, limit 5, zdjęcie/podmiana | Pełna droga od wylosowania do potwierdzonego zdjęcia i nowego losowania |
| MUST | Galeria, komentarze, oceny w dwóch kategoriach, moderacja | Widoczna interakcja kilku kont, egzekwowana serwerowo |
| MUST | Adapter Google Drive, lokalny adapter testowy, odzyskiwanie po błędach | Testy kontraktowe i udokumentowany test live albo jawny brak jego wykonania |
| MUST | Zamknięcie i czyszczenie, minimalne archiwum | Dane A znikają, dane B pozostają, album A nie jest automatycznie usuwany |
| SHOULD | Drobne usprawnienia formularzy i widoków pustych, wygodne filtry galerii | Nie mogą opóźniać MUST; podstawowa używalność i dostępność są obowiązkowe |
| LATER | SMS, push, OneDrive, drużyny gry, ranking, live WebSocket, szersze testy obciążenia | Nie dodawać implementacji do pierwszego PoC |
| OUT | Samodzielna rejestracja, PESEL/e-mail w bazie uczestników, publiczna galeria podczas gry, pełny CRM, import harmonogramu, natywna aplikacja | Brak tych przepływów i niepotrzebnych danych |

PoC jest etapowany technicznie, ale zakończenie samego pierwszego pionowego wycinka nie oznacza ukończenia całego zakresu MUST.


Szczegółowe kryteria i scenariusze: sekcje 5–14 specyfikacji.
