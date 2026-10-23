# Współpraca przy appce eventowej

Repo jest publiczne, ale **prawo zapisu i merge mają wyłącznie osoby z odpowiednimi uprawnieniami**. Każdy może zgłosić Issue lub zaproponować PR z forka; taki PR nie oznacza automatycznej akceptacji wkładu.

## Praca nad PoC

1. **Przed kodowaniem:** przeczytaj [POC_START_HERE.md](docs/POC_START_HERE.md), [requirements.md](docs/requirements.md) i [poc-readiness.md](docs/poc-readiness.md). Nie przesądzaj zakresu lub technologii przed decyzją właściciela.
2. **Praca:** ustal właściwe Issue, załóż osobną gałąź od aktualnego `main` i ogranicz PR do jednego logicznego tematu.
3. **Zmiany:** podaj, co i dlaczego zmieniłeś, jak sprawdziłeś działanie oraz jakie testy rzeczywiście wykonałeś. Brak możliwości przetestowania należy jawnie zaznaczyć.
4. **Decyzje:** nowa funkcja/zmiana granic MVP → aktualizacja `docs/requirements.md`; ważna decyzja technologiczna → ADR w `docs/decisions/`.
5. **Reuse:** jeżeli przenosisz kod Poligonu lub gry fotograficznej, wpisz źródłowy repo, commit, ścieżkę, autorów, modyfikacje oraz kwestie zależności/licencji; patrz [source-provenance.md](docs/source-provenance.md).
6. **Bezpieczeństwo:** dane testowe wyłącznie syntetyczne; nie commituj sekretów, baz użytkowników ani zdjęć. Testuj izolację co najmniej dwóch eventów i przypadki odmowy uprawnień.
7. **Review i merge:** obowiązujący Ruleset chroni default branch, `develop` oraz `release/*`: PR, co najmniej 1 świeża akceptacja, rozstrzygnięte review threads, wyłącznie **squash merge**. Ownerzy mają wyjątek jedynie **przez PR**. Nie wykonuj force-push ani zwykłego push na chronione gałęzie.
8. **Wdrożenie:** lokalne instrukcje/testy są potrzebne; nie tworzymy produkcyjnego deploymentu przez GitHub Actions. Docelowe CI jest zewnętrzne i będzie ustalone osobno.

## Definicja ukończenia PR implementacyjnego

- [ ] Funkcja jest w zatwierdzonym zakresie albo ma jawną zgodę na zmianę zakresu.
- [ ] Zaktualizowano wymagania/ADR, jeśli są potrzebne.
- [ ] Dodano adekwatne testy (w tym negatywne przypadki izolacji eventu/RBAC, gdy dotyczą zmiany).
- [ ] Opisano sposób lokalnego uruchomienia oraz weryfikacji na danych fikcyjnych.
- [ ] Nie dodano danych osobowych, zdjęć, poświadczeń ani niezamierzonych zależności produkcyjnych.
- [ ] Dokumentacja reuse/atrybucji jest kompletna, jeżeli przeniesiono kod.

Nie zakładamy zespołów o konkretnych slugach w `CODEOWNERS`, dopóki Owner organizacji nie zweryfikuje faktycznych Teams i uprawnień. Wymóg akceptacji PR wynika z Rulesetu, niezależnie od `CODEOWNERS`.
