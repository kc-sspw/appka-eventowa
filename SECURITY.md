# Bezpieczeństwo — appka-eventowa

To jest repozytorium **planowanego produktu**, obecnie bez kodu wykonawczego. Ogólna polityka organizacji: [kc-sspw/.github/SECURITY.md](https://github.com/kc-sspw/.github/blob/main/SECURITY.md).

## Zgłaszanie problemów

Podejrzenia wycieku poświadczeń, naruszenia prywatności uczestników i błędów autoryzacji kieruj prywatnie na **kc@samorzad.pw.edu.pl**. Nie dodawaj sekretów, danych osobowych, zrzutów prywatnych profili ani szczegółów aktywnego incydentu do Issues lub PR, szczególnie w publicznych repozytoriach referencyjnych.

## Zasady PoC

- Dane i uprawnienia muszą być izolowane per wydarzenie; nie kopiujemy globalnego broadcastu ani publicznych odpowiedzi zawierających dane osobowe.
- Minimalizujemy dane uczestników, stosujemy autoryzację po stronie serwera i sprawdzamy dostęp do każdego obiektu.
- Zdjęcia i pliki użytkowników nie mogą być domyślnie publicznie cache'owane; polityka retencji, zgody i dostęp muszą zostać ustalone przed użyciem prawdziwych danych.
- Żadnych sekretów w repo, testach, logach, obrazach ani historii. Zastępuj je wyłącznie nazwami zmiennych i bezpiecznymi przykładami.
- Ujawniony sekret traktujemy jako przejęty: w razie rzeczywistego użycia najpierw rotacja/unieważnienie, potem analiza skutków. Nie przepisujemy historii bez osobnej decyzji.
- Nie wdrażamy ani nie uruchamiamy produkcyjnych workflowów w ramach przeglądu źródeł.
- Nie kopiujemy kodu repozytoriów referencyjnych bez potwierdzenia praw; niezależna implementacja zachowania jest dozwoloną drogą po zatwierdzeniu specyfikacji.

Zidentyfikowane warunki rozpoczęcia PoC: [bramki PoC](docs/poc-readiness.md). Analiza referencji: [przegląd 2026-10-21](docs/reviews/2026-10-21-security-review.md).
