# Gotowość PoC — stan implementacji 24.10.2026

Zakres i architektura zostały zatwierdzone: [wymagania](requirements.md),
[specyfikacja](IMPLEMENTATION_PROMPT.md), [ADR](decisions/README.md).
Implementacja jest proponowana przez draft PR #6; nie została wdrożona produkcyjnie.

## Lokalny PoC na danych syntetycznych

- [x] Django/PostgreSQL, migracje, lokalny Compose i dwa odizolowane wydarzenia.
- [x] Konta i role per host, grupy, import/eksport XLSX bez przesyłania arkusza.
- [x] Aktualności, stałe informacje i harmonogram z filtrowaniem odbiorców.
- [x] Gra, limit pięciu aktywnych, podmiana, galeria, oceny i komentarze.
- [x] Prywatny magazyn lokalny oraz adapter Drive/OAuth z testami kontraktowymi.
- [x] Moderacja, retry, budżet i zamknięcie zachowujące aktualny album.
- [x] Testy PostgreSQL, współbieżności i Chromium w CI; szczegóły i aktualny commit w [raporcie](testing.md).
- [x] Instrukcje startu, organizatora i administratora.
- [x] Brak automatycznego deploymentu, maili i SMS; źródła i zależności opisane.

Kod jest gotowy do przeglądu jako lokalny PoC, nie jako potwierdzona integracja
live ani system przetestowany pod dużym obciążeniem.

## Przed realnym pilotem — nadal do wykonania

- [ ] Review kodu i akceptacja PR zgodnie z Rulesetem.
- [ ] Live Google OAuth/upload/download/podmiana/usunięcie na testowym koncie organizatora.
- [ ] Cofnięcie zgody i odnowienie jej na tym samym koncie/folderze; sprawdzenie trybu publikacji OAuth.
- [ ] Domena, wildcard TLS, reverse proxy, prawidłowy adres klienta dla limitowania prób i limit body.
- [ ] Zasady danych, zgód uczestników, konta chmurowego organizatora i udostępnienia albumu.
- [ ] Uprawnienia repo/CI/środowiska docelowego oraz sekrety poza repo.
- [ ] Telefony iOS/Android, Safari, rzeczywista sieć wyjazdowa i przerwania połączeń.
- [ ] Uzgodniony ruch pilota, test równoczesnych uploadów oraz limity konta Google/API.
- [ ] Retencja logów infrastruktury, backup/restore i ponowne czyszczenie zamkniętych eventów.
- [ ] Ustalone wsparcie operatora, postępowanie przy błędach i osobna zgoda na wdrożenie.

Album zostaje własnością organizatora. Aplikacja nie udostępnia go publicznie
ani nie kasuje po 30 dniach. Przykładowe siedem dni po wydarzeniu to decyzja
organizacyjna właściciela albumu, nie timer aplikacji.

Historyczny [audyt referencji](reviews/2026-10-21-security-review.md) pozostaje
niezmieniony; nie jest audytem bezpieczeństwa tej nowej implementacji.
