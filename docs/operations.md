# Administracja i utrzymanie PoC

## Platforma

Panel `/admin/` działa wyłącznie na `PLATFORM_HOST`. Pierwsze konto twórz przez
`manage.py createsuperuser`; jest to rola PLATFORM bez wydarzenia. Utwórz Event
ze slugiem DNS (małe litery, cyfry, myślniki), datami i nazwą. Slug jest trwały.
Następnie utwórz Account, wybierz ten event i rolę ORGANIZER, ustaw mocne hasło;
formularz proponuje losowy login. Przekaż dane organizatorowi własnym kanałem.
Organizator nie ma dostępu do Django admin ani uprawnień platformowych.

`DRAFT → ACTIVE → CLOSING → CLOSED`. Aktywację wykonuje organizator w panelu.
Koniec wydarzenia jest sprawdzany na każdym request, więc opóźnienie workera nie
przedłuża dostępu. Zamknięty slug pozostaje zarezerwowany. Nie usuwaj rekordów
Event przez bezpośredni SQL: ominąłbyś rozliczenie operacji w chmurze.

## Konfiguracja Google

1. W projekcie Google Cloud włącz Drive API i skonfiguruj ekran zgody OAuth
   zgodnie z kontami używanymi do testów; w trybie testowym dodaj testowych użytkowników.
2. Utwórz klienta OAuth typu **Web application**. Zarejestruj dokładny URI:
   `PUBLIC_SCHEME://PLATFORM_HOST[:PUBLIC_PORT]/oauth/callback`.
3. Ustaw `STORAGE_BACKEND=drive`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   i `TOKEN_KEY` (32 bajty jako klucz Fernet). Sekrety trzymaj poza repo.
4. Ustaw prawdziwe `EVENT_DOMAIN`, `PLATFORM_HOST`, `PUBLIC_SCHEME=https`.
   W produkcji usuń lokalny port; lokalny test Google wymaga callbacka akceptowanego
   w konfiguracji klienta, nie zakładaj akceptacji dowolnej subdomeny localhost.
5. Przeładuj web i worker. Organizator łączy swoje konto ze swojego hosta eventu.

Zakres: `https://www.googleapis.com/auth/drive.file`. Aplikacja nie prosi o pełny
Drive, nie tworzy publicznych permissions, nie używa konta serwisowego ani
Shared Drives. Folder i pliki mają właściwości aplikacji z UUID wydarzenia;
przed odczytem/usunięciem adapter weryfikuje folder i event, a przy odzyskiwaniu
również UUID operacji. Nazwy plików są losowe, bez imion i oryginalnych nazw.

OAuth: losowy state, PKCE S256, krótki termin, jednorazowy callback i powrót na
oryginalny host z biletem związanym z sesją organizatora. Tokeny są szyfrowane
Fernet. Nie zmieniaj `TOKEN_KEY` bez procedury migracji: utracisz możliwość
odszyfrowania istniejących połączeń. Aplikacja nie przechowuje tokenu w przeglądarce.

W trybie External/Testing refresh token dla używanego zakresu może wygasać po
siedmiu dniach. To limit trybu OAuth, nie retencja zdjęć. Przed pilotem sprawdź
aktualną konfigurację publikacji i warunki Google. Nie wykonano live testu konta.

Po zamknięciu usuwamy lokalne tokeny, ale nie robimy globalnego revoke zgody
Google, który mógłby uszkodzić inne eventy tego samego konta. Właściciel może
ręcznie odłączyć aplikację w ustawieniach bezpieczeństwa konta Google dopiero
po zakończeniu wszystkich powiązanych wydarzeń.

Źródła pierwotne zweryfikowane przy implementacji:
[zakresy](https://developers.google.com/workspace/drive/api/guides/api-specific-auth),
[upload i prealokowane ID](https://developers.google.com/workspace/drive/api/guides/manage-uploads),
[OAuth](https://developers.google.com/identity/protocols/oauth2).

## Worker i odzyskiwanie

```bash
docker compose exec worker python manage.py storage_worker --once
docker compose logs --tail 50 worker
```

Normalny worker wykonuje cykl co pięć sekund. Kolejka jest w PostgreSQL:
UUID operacji, status, liczba prób, termin retry i dzierżawa z tokenem chroniącym
przed starym workerem. Kolejność blokad: Event → Assignment; wywołania Drive są
poza transakcją. Serializacja po evencie jest świadomym kompromisem małego PoC.

Upload rezerwuje do 1 MiB i zapisuje prealokowane ID pliku **przed** wysłaniem.
Po timeout worker szuka tego samego ID/UUID operacji; nie tworzy kolejnej kopii.
Nie przechowujemy binariów w kolejce. Jeżeli plik nie dotarł, status NEEDS_INPUT
zwalnia rezerwację, a użytkownik wybiera obraz ponownie. Restart procesu nie
traci trwałego zapisu operacji. Stare wejściowe pliki tymczasowe usuwa worker po godzinie.

Przy podmianie commit przełącza zdjęcie i zleca usunięcie poprzedniego. Pending
delete nadal liczy się do budżetu. `404` dostawcy oznacza osiągnięty cel usunięcia.
`RETRY` stosuje backoff; panel organizatora pozwala przyspieszyć ponowienie w
aktywnym evencie. Dla CLOSING platforma ma akcję **Ponów porządkowanie zamykanych
wydarzeń**; respektuje ona aktywne dzierżawy i terminy retry. Worker kontynuuje
próby automatycznie. Nie zeruj rekordów kolejki, żeby „naprawić” licznik miejsca.

Zamknięcie usuwa zbędne dane także przy awarii Drive. Pozostają jedynie minimalne
operacje, połączenie i token potrzebne do dokończenia usunięć. Stan CLOSED jest
osiągany dopiero po ich rozliczeniu. Gotowe aktualne pliki albumu nie są usuwane.
Po CLOSED pozostaje UUID, slug, nazwa, daty i cleaned_at; pola techniczne mają
neutralne wartości, bez danych gry, kont, folderu czy tokenu.

## Prywatność i środowisko docelowe

Brak publicznego MEDIA_URL, service workera, localStorage, zewnętrznych skryptów
importu i analityki. Odczyt zdjęć przechodzi przez autoryzację wydarzenia;
prywatne odpowiedzi mają `private, no-store`. Miniatury: prywatny cache do godziny,
do 256 MiB, czyszczony przy podmianie, moderacji i zamknięciu.

Lokalny Compose jest dostępny tylko na interfejsie loopback. Przed pilotem
potrzebny jest wildcard DNS/TLS oraz zaufany reverse proxy. `TRUST_PROXY_TLS=1`
włączaj wyłącznie, gdy proxy zastępuje `X-Forwarded-Proto`, a Gunicorn nie jest
bezpośrednio dostępny z Internetu. Aplikacja nie ufa `X-Forwarded-Host`.
`DEBUG=0` wymusza HTTPS i secure cookies oraz odrzuca FakeStorage.

Proxy powinno limitować body do ok. 16 MiB i czas requestów. Serwer dodatkowo
odcina pliki powyżej 15 MiB, waliduje format i piksele. Nie wystawiaj `.private`,
CSV, bazy ani wolumenów jako statycznych plików. Zachowaj oddzielne hosty platformy
i wydarzeń. Rate limiting po IP używa REMOTE_ADDR: przy proxy bez normalizacji
adresu wszystkie osoby dzielą kubełek IP, co trzeba dostroić przed pilotem.

Gunicorn nie ma access logu, aplikacja nie loguje payloadów ani wyjątków Google.
Ogranicz logi infrastruktury do 7 dni; wyłącz query string callbacka i treści
requestów. Jest to wymaganie wdrożeniowe, nie skonfigurowana tu infrastruktura.
PoC nie tworzy backupów. Proponowany docelowy backup: szyfrowany, maks. 7 dni;
po restore ponownie usuń dane CLOSED **przed** udostępnieniem systemu.

Testy i CI używają wyłącznie syntetycznych danych. Produkcyjne wdrożenie pozostaje
poza GitHub Actions. Review i squash merge odbywają się przez istniejący Ruleset.

## Wyjątkowe ręczne rozliczenie usunięcia

Jeżeli token został trwale cofnięty, a wydarzenie jest już CLOSING, zwykły retry
może nie wystarczyć. Operator z dostępem do serwera może odczytać UUID operacji
DELETE i jej `external_file_id` z `StorageOperation` dla tego wydarzenia.
Właściciel konta musi niezależnie sprawdzić na Drive, że **ten konkretny plik**
nie istnieje (lub trwale go usunąć). Dopiero wtedy operator może wykonać:

```bash
docker compose exec web python manage.py confirm_storage_absence SLUG UUID_OPERACJI --file-id DOKLADNE_ID_PLIKU --verified-absent
```

Komenda wymaga CLOSING, oczekującego DELETE, zgodnego ID pliku i wygasłej dzierżawy.
Rozlicza tylko jedną wskazaną operację; nie usuwa ani nie uznaje za usunięty całego
albumu. Jest świadomym potwierdzeniem operatora, **nie automatycznym dowodem z API**.
Nie używaj jej tylko po to, by zmienić status na CLOSED. Pozostałe operacje muszą
zostać rozliczone normalnie.
