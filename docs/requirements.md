# Wymagania — Appka eventowa

## Kontekst źródłowy

Projekt występuje w materiałach jako „Aplikacja wyjazdowa + BeReal” oraz „appka wyjazdowa”. Repozytorium używa nazwy `appka-eventowa`.

## Cel pierwszego etapu

Zamknąć MVP jednego produktu obsługującego wiele oddzielnych wyjazdów/eventów i przygotować kryteria pilotażu.

## Zakres potwierdzony

- wiele oddzielnych wyjazdów/eventów,
- izolacja pomiędzy równoległymi wyjazdami,
- role,
- harmonogram,
- lista uczestników,
- zdjęcia przypisane do konkretnego wyjazdu,
- robocza reguła usuwania zdjęć po 30 dniach od zakończenia wyjazdu.

## Do potwierdzenia

- dokładny zakres logowania i ról,
- priorytety funkcji MVP,
- zasady dostępu do zdjęć,
- dokładna polityka retencji i moment startu 30-dniowego okresu,
- kryteria pilotażu.

## Zależności

- decyzje organizatorów wyjazdów,
- zasady przetwarzania danych uczestników i zdjęć,
- potwierdzony scenariusz pilotażowy.

## Kryteria odbioru pierwszego etapu

- zakres MVP jest zapisany i zaakceptowany,
- scenariusz dwóch równoległych wyjazdów jest opisany,
- wymagania dotyczące harmonogramu i uczestników są jednoznaczne,
- decyzja o retencji zdjęć jest potwierdzona.

Nie dokładamy funkcji bez materiału źródłowego lub jawnej decyzji projektowej.

## Kolejny etap: zamknięcie zakresu PoC

**Status 23.10.2026:** poniższa tabela **nie jest jeszcze specyfikacją wykonawczą**. Właściciel projektu przedstawi szczegółowy opis docelowych procesów w kolejnym czacie. Do tego czasu nie zakładamy liczby ekranów, stacku, dostawcy tożsamości, integracji produkcyjnych ani tego, że wszystkie moduły referencji mają znaleźć się w MVP.

| Decyzja do zapisania | Status | Uwagi |
|---|---|---|
| Rola/typy użytkowników oraz możliwość należenia do kilku eventów | Otwarta | Wymagane kontrole po stronie backendu |
| Tworzenie wydarzenia, zaproszenia, dołączanie/opuszczanie | Otwarta | Szczegółowy przebieg poda właściciel |
| Scenariusze harmonogramu i komunikatów | Otwarta | Referencja: Poligon |
| Dokładna mechanika fotografii (inspiracja BeReal / zadania / oceny / inne) | Otwarta | Nie przesądzać rozwiązania z gry referencyjnej |
| Zgody, widoczność zdjęć i retencja | Otwarta | 30 dni po zakończeniu eventu to hipoteza |
| Model eventu, integracje, stack oraz local setup | Otwarta | Rozstrzygnięcie po wyborze minimalnego pionowego wycinka |
| Zakres prototypu lokalnego vs pilotaż dla uczestników | Otwarta | Różne progi bezpieczeństwa |
| Wymagania dotyczące UI, dostępności i urządzeń | Otwarta | Aplikacja webowa; detale nieustalone |

### Scenariusze obowiązkowe niezależnie od wybranych funkcji

- Dwa wydarzenia są obsługiwane jednocześnie, a operacje i zasoby mają prawidłowy event scope.
- Konto A nie może czytać ani edytować zasobów wydarzenia B (API, pliki, ewentualny realtime).
- Uprawnienia użytkownika nie są określane wyłącznie przez pola przekazane w formularzu albo request body.
- PoC można uruchomić i przetestować **lokalnie na danych syntetycznych**, bez produkcyjnego dostępu do SSPW.

Zatwierdzony zakres zapisujemy jako **MUST / SHOULD / LATER / OUT** z kryteriami odbioru. Mapa komponentów jest w [reference-inventory.md](reference-inventory.md), a procedura pracy z kolejnym chatem w [POC_START_HERE.md](POC_START_HERE.md).

Nie przenosimy całych rozwiązań Poligon ani SSPWPhotoTaskGame 1:1 bez analizy ich zabezpieczeń i dopasowania do zatwierdzonych wymagań.
