# Bezpieczeństwo — appka eventowa

**Stan 23.10.2026:** publiczne repo docelowego produktu, nadal bez kodu aplikacji. Polityka ogólna organizacji: [kc-sspw/.github/SECURITY.md](https://github.com/kc-sspw/.github/blob/main/SECURITY.md).

## Prywatne zgłaszanie problemów

Podejrzenia naruszenia prywatności uczestników, wycieku poświadczeń, błędów autoryzacji lub dostępu między eventami zgłaszaj **prywatnie** na **kc@samorzad.pw.edu.pl**. Nie wklejaj tokenów, zdjęć uczestników, pełnych danych osobowych, prywatnych URL-i, logów zawierających wrażliwe dane ani szczegółów aktywnego incydentu do publicznych Issues, PR i komentarzy.

## Zasady obowiązujące od pierwszego commita kodu

- **Wieloeventowość i autoryzacja:** każda operacja po stronie serwera musi sprawdzać rolę, członkostwo i właściwy event. Filtr wyłącznie po stronie frontendu nie zapewnia izolacji.
- **Minimalizacja danych:** tylko pola rzeczywiście potrzebne do funkcji i uprawnionej roli. Nie zwracaj całej encji uczestnika przez ogólnodostępny endpoint.
- **Pliki i zdjęcia:** nie udostępniaj ich przez publiczny katalog ani statyczny cache PWA. Dostęp i pobranie pliku wymagają uprawnień; retencję i zasady zgód zatwierdzimy przed prawdziwymi danymi.
- **Sekrety:** nie commituj kluczy, `.env`, tokenów, certyfikatów, kont serwisowych, baz danych, prywatnych zdjęć, logów i zrzutów zapasowych. Jeśli aktywny sekret został ujawniony, wymaga unieważnienia/rotacji.
- **Referencje:** właściciel potwierdził prawa do wykorzystania kodu Poligonu i gry zdjęciowej. Nadal stosujemy atrybucję, sprawdzamy zależności i **nie przenosimy** wprost ich historycznych ustawień dostępu, globalnego WebSocket czy danych startowych.
- **Środowiska:** do pierwszego PoC używamy danych syntetycznych. Nie wykonujemy wdrożeń produkcyjnych przez GitHub Actions; wdrożenia obsłuży odrębne CI po osobnej decyzji.
- **Zmiany:** praca przez PR z review i testami; nie omijać ochrony `main` zwykłymi pushami.

Dalsze bramki: [poc-readiness.md](docs/poc-readiness.md). Rejestr historycznego statycznego audytu: [przegląd 2026-10-21](docs/reviews/2026-10-21-security-review.md).

**To, że repo jest publiczne, nie oznacza, że baza, media, prawdziwe dane testowe i środowisko pilotażu mogą być publiczne.**
