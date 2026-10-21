# Appka eventowa

Projekt Komisji Cyfryzacji SSPW na kadencję 2026/2027. W dotychczasowych materiałach projekt występuje jako **appka wyjazdowa / Aplikacja wyjazdowa + BeReal**.

## Cel

Przygotować jeden minimalny produkt możliwy do wykorzystania przy wielu oddzielnych wyjazdach/eventach.

## Aktualny stan

Etap doprecyzowania MVP i przygotowania pilotażu.

## Zakres potwierdzony w źródłach

- obsługa wielu oddzielnych wyjazdów/eventów,
- izolacja danych i kontekstu pomiędzy równoległymi wyjazdami,
- role,
- harmonogram,
- lista uczestników,
- zdjęcia przypisane do konkretnego wyjazdu,
- robocza reguła usuwania zdjęć po 30 dniach od zakończenia wyjazdu.

Szczegółowe priorytety funkcji nadal wymagają potwierdzenia.

## Minimalny zakres pierwszego etapu

Zamknąć MVP i kryteria pilotażu, a następnie zweryfikować co najmniej dwa równoległe wyjazdy/eventy.

## Zależności

- potwierdzony zakres MVP,
- organizatorzy pilotażu,
- zasady przetwarzania danych uczestników i zdjęć,
- decyzje dotyczące retencji danych.

## Następny krok

Zamknąć zakres MVP i kryteria pilotażu w [wymaganiach](docs/requirements.md).

## Materiał referencyjny: Poligon

W organizacji znajduje się również [`apka-wyjazdowa`](https://github.com/kc-sspw/apka-wyjazdowa) — kod wcześniejszego projektu **Poligon** (backend Spring Boot i klient Flutter). To **prototyp referencyjny**, a nie drugie główne repo projektu KC.

Przed wykorzystaniem fragmentów tego kodu trzeba zweryfikować prawa do jego użycia, bezpieczeństwo oraz zgodność z ustalonym MVP. Nie traktujemy istniejącego stosu technologicznego ani funkcji Poligon jako decyzji architektonicznej Komisji. Zakres oceny jest w [Issue #2](https://github.com/kc-sspw/appka-eventowa/issues/2).

## Bramka bezpieczeństwa przed PoC

Rozpoczęcie PoC i adaptacja referencji są uzależnione od [warunków bezpieczeństwa PoC](docs/poc-readiness.md) oraz [przeglądu źródeł z 21.10.2026](docs/reviews/2026-10-21-security-review.md). Repozytorium nadal nie zawiera kodu aplikacji ani konfiguracji wdrożeniowej.

## Dokumentacja

- [Wymagania](docs/requirements.md)
- [Decyzje architektoniczne](docs/decisions/README.md)
- [Contributing](CONTRIBUTING.md)

Technologia nie jest na tym etapie narzucona.
