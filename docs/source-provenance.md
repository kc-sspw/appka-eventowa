# Pochodzenie referencji, uprawnienia i atrybucja

**Stan decyzji: 23.10.2026.** Właściciel projektu potwierdził w rozmowie: **„mamy prawo do kodu”** w kontekście adaptacji Poligonu i gry fotograficznej. Dopuszczamy analizę oraz przygotowanie do ponownego wykorzystania, ale **nie utożsamiamy tego stwierdzenia z publiczną licencją dla osób trzecich** i nie dopisujemy do referencji nieistniejącej licencji. W każdym konkretnym reuse zachowujemy atrybucję i sprawdzamy pochodzenie/licencje zależności.

| Referencja | Ustalony kontekst i autorstwo | Co zapisać przy adaptacji |
|---|---|---|
| [kc-sspw/apka-wyjazdowa](https://github.com/kc-sspw/apka-wyjazdowa) | Import projektu **Poligon**, utworzony 19.10.2026 jako repo `fork: false`; nagłówki wybranych plików wskazują **Łukasza Piętkę (FUT 2025)**. | Pochodzenie każdego kopiowanego pliku, commit, autorzy, sposób adaptacji, zgodność z architekturą multi-event i zależności zewnętrzne. |
| [Korniszon99/SSPWPhotoTaskGame](https://github.com/Korniszon99/SSPWPhotoTaskGame) | Repozytorium gry zdjęciowej PHP/PWA; powiązane ze starszym PWGame. | Zidentyfikować kopiowane pliki, autorów i ewentualnych współtwórców; zachować informacje o atrybucji oraz separować kod od zdjęć/danych uczestników. |
| [Korniszon99/PWGame](https://github.com/Korniszon99/PWGame) | Historyczna implementacja funkcji fotograficznych. | Rozpatrywać wyłącznie konkretne potrzebne elementy. **Nie kopiować** opisanych historycznych danych startowych/default credentials. |

W chwili wcześniejszego audytu w repozytoriach nie znaleziono jednoznacznych plików `LICENSE`/`COPYING`. To nie dowodzi braku wszystkich uprawnień; przeciwnie, obecne potwierdzenie właściciela pozwala rozpocząć ocenę i adaptację, ale **wybór licencji dla nowej aplikacji i upublicznionych komponentów pozostaje osobną decyzją**.

**Mechanika inspirowana „BeReal”** dotyczy koncepcji zachowania. Nie mamy tutaj potwierdzenia prawa do kodu, logotypów, marki, wzornictwa czy treści zewnętrznego produktu BeReal. Własną funkcję tworzymy bez kopiowania zastrzeżonych zasobów tego produktu.

## Co dokumentować podczas implementacji

Przy adaptacji komponentu do nowego repo uzupełnij (w PR lub dedykowanym pliku):
- referencja: repo, ścieżka, SHA commita lub tag;
- autorzy i inne notice/licencje z plików źródłowych;
- zakres kopiowania, modyfikacji, ewentualny sposób zachowania informacji o autorze;
- czy rozwiązanie zachowuje izolację eventów, poprawną autoryzację i zasady prywatności;
- czy dodaje zależności z licencjami i obowiązkami dystrybucyjnymi;
- co świadomie **nie zostało** przejęte.

Nie pobieraj żadnych rzeczywistych zdjęć, kont, baz, poświadczeń, logów ani zrzutów z referencji do nowego repo. Zgodnie z informacją właściciela ujawniony w historycznej konfiguracji Poligonu login/hasło były **testowe**; nie traktujemy ich jako aktualnego blokera koncepcyjnego PoC, ale nie kopiujemy ich wartości.

## Status

- [x] Właściciel potwierdził możliwość korzystania z kodu referencyjnego (23.10.2026).
- [ ] Przypisać pliki i autorów do **konkretnych** adaptowanych modułów (po zatwierdzeniu zakresu).
- [ ] Potwierdzić zobowiązania wynikające z zależności zewnętrznych przy konkretnym reuse.
- [ ] Uzgodnić licencję i zasady publicznej redystrybucji **nowej** aplikacji.
- [ ] Ustalić zasady zdjęć uczestników odrębnie od praw do kodu.

Mapa funkcji do oceny: [reference-inventory.md](reference-inventory.md). Bezpieczeństwo integracji: [poc-readiness.md](poc-readiness.md).
