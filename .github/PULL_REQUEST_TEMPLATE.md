## Cel i powiązane Issue

Co zmienia ten PR, dlaczego i na podstawie jakiej zaakceptowanej potrzeby / Issue?

## Zakres zmian

Opisz funkcje, API, model danych i konsekwencje dla istniejących eventów.

## Jak sprawdzono?

Podaj **rzeczywiście wykonane** komendy testowe i wyniki. Wymień nieprzetestowane części oraz wymagania środowiskowe.

## Źródła i atrybucja (jeśli adaptowano kod)

Repo źródłowe, ścieżki, commit SHA, autorzy/notices i zakres modyfikacji albo „nie dotyczy”.

## Checklista

- [ ] Zmiana mieści się w zatwierdzonym zakresie PoC lub jest jawnie zaakceptowana.
- [ ] Nie ma sekretów, prawdziwych danych uczestników, zdjęć ani baz.
- [ ] Zaktualizowano wymagania lub ADR, jeśli zmienił się zakres lub architektura.
- [ ] Przetestowano dostęp per event i odmowę dostępu do cudzych zasobów, jeśli PR zmienia logikę uprawnień/danych.
- [ ] Opisano działanie lokalne na danych fikcyjnych i sposób weryfikacji.
- [ ] Nie dodano produkcyjnego workflow GitHub Actions/deploymentu.
- [ ] Wszystkie review threads są zamknięte; PR można scalić przez squash.

**Ruleset:** `main`, `develop` i `release/*` są chronione. Wymagana akceptacja innej osoby, z wyjątkiem PR-only bypass dla Ownerów organizacji.
