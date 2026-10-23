# Appka eventowa — KC SSPW

**Status: przygotowanie zakresu PoC.** Główne repozytorium planowanego produktu Komisji Cyfryzacji SSPW (2026/2027). W starszych materiałach występuje jako **appka wyjazdowa** lub **„Aplikacja wyjazdowa + BeReal”** — ta druga nazwa opisuje pomysł na mechanikę fotograficzną, nie współpracę z firmą BeReal.

> **Następny krok:** [POC_START_HERE.md](docs/POC_START_HERE.md) — kompletne przekazanie kontekstu do następnego chatu, w którym właściciel opisze szczegółową wizję, dobierzemy elementy Poligonu i gry fotograficznej, a później powstanie prompt dla osobnego chatu implementacyjnego.

## Cel produktu

Jedna aplikacja webowa, która może obsługiwać **wiele niezależnych wyjazdów i wydarzeń jednocześnie**. Dotychczasowy zakres źródłowy obejmuje role, harmonogram, uczestników, zdjęcia oraz informacje/komunikaty przypisane do konkretnego wydarzenia. Mechanika fotograficzna inspirowana BeReal jest do rozstrzygnięcia podczas definiowania PoC.

Robocza reguła retencji zdjęć: **30 dni po zakończeniu wydarzenia** — to propozycja, nie decyzja. Powiadomienia push nie są wymagane w pierwszym PoC. **Szczegółowy zestaw funkcji, ekrany, technologie i priorytety nie zostały jeszcze zatwierdzone.**

## Stan repozytorium

- Repo jest **publiczne**: kod i historia są dostępne do odczytu, ale prawo zapisu wynika z uprawnień Teams i współpracowników, nie z publicznej widoczności.
- Gałęzie `main`, `develop` i `release/*` są objęte repozytoryjnym Rulesetem **KC SSPW — protected main**, z wymaganym PR, akceptacją i squash merge. Ownerzy organizacji mają bypass **wyłącznie przez PR**.
- Na tym etapie repo **zawiera dokumentację i szablony współpracy, nie kod aplikacji**. Nie ma jeszcze uzgodnionego stosu technologicznego, uruchomienia ani deploymentu.
- Produkcyjne wdrożenia będą organizowane przez **zewnętrzną infrastrukturę CI**, nie GitHub Actions; do rozpoczęcia lokalnego PoC nie trzeba dostępu produkcyjnego.
- Projektowy spike/prototyp na danych syntetycznych może ruszyć po uzgodnieniu minimalnego scenariusza. PoC z prawdziwymi uczestnikami wymaga oddzielnej decyzji i spełnienia warunków bezpieczeństwa.

## Referencje (nie repo produktu)

- [Poligon — kc-sspw/apka-wyjazdowa](https://github.com/kc-sspw/apka-wyjazdowa): Spring Boot, Flutter, harmonogram, załoga, ogłoszenia, zadania i WebSocket.
- [SSPWPhotoTaskGame](https://github.com/Korniszon99/SSPWPhotoTaskGame): PHP/PWA, wyzwania i zdjęcia, oceny, ranking, panel administratora.
- [PWGame](https://github.com/Korniszon99/PWGame): starsze rozwiązanie, wyłącznie jako dodatkowy kontekst.

Właściciel potwierdził prawo do korzystania z kodu referencyjnego; przy rzeczywistym kopiowaniu trzeba zachować autorstwo, zidentyfikować źródłowe pliki i zależności zewnętrzne. **Nie kopiujemy wprost istniejących konfiguracji bezpieczeństwa ani danych testowych/produkcyjnych.** Szczegóły: [mapa modułów](docs/reference-inventory.md) i [pochodzenie](docs/source-provenance.md).

## Wymagania i zasady pracy

- [Rozpocznij PoC / przekazanie do nowego chatu](docs/POC_START_HERE.md)
- [Wymagania i otwarte decyzje](docs/requirements.md)
- [Kandydaci do adaptacji z referencji](docs/reference-inventory.md)
- [Kryteria bezpieczeństwa PoC](docs/poc-readiness.md)
- [Statyczny przegląd źródeł z 21.10.2026](docs/reviews/2026-10-21-security-review.md)
- [Pochodzenie i wykorzystanie kodu](docs/source-provenance.md)
- [Decyzje architektoniczne (ADR)](docs/decisions/README.md)
- [Współpraca i pull requesty](CONTRIBUTING.md)
- [Zgłaszanie problemów bezpieczeństwa](SECURITY.md)

Zadania do kontynuacji: [Issue #1 — zakres MVP i pilotaż](https://github.com/kc-sspw/appka-eventowa/issues/1), [Issue #2 — ocena Poligonu](https://github.com/kc-sspw/appka-eventowa/issues/2).

**Granica danych:** kod może być publiczny; sekrety, bazy z danymi użytkowników, zdjęcia uczestników, kopie zapasowe i dostęp do infrastruktury muszą pozostać poza publicznym Git.
