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


## Implementacja PoC — 24.10.2026

Nowy kod Python/HTML/CSS/JS napisano dla zatwierdzonego kontraktu Django. Nie
kopiowano bloków PHP, Java, Flutter, konfiguracji, zdjęć ani baz referencji.
Reuse dotyczy zachowań produktu, opisanych w sekcji 12 [specyfikacji](IMPLEMENTATION_PROMPT.md):

| Referencja przypięta w specyfikacji | Wykorzystane zachowanie | Nowa implementacja |
|---|---|---|
| SSPWPhotoTaskGame `77046c6806a6b09fa7442f7df11ccae1123f4b9f`: `photo_game/actions/draw_task.php`, `database/database.php` | Zadanie → przydział → zdjęcie, pięć niewykonanych | `game/services.py`, blokada Event i brak powtórek |
| Ten sam commit: `elements/user_task_list_grid.php`, `gallery.php` | Karty własnych zadań i galeria 24 zdjęć | Własne templates/CSS, prywatne URL, bez rankingu |
| Ten sam commit: `actions/upload_photo.php`, `rate_photo.php`, `admin_delete_photo.php`, `js/ratings.js` | Kompresja, oceny i moderacja | Nowy pipeline, API, wersjonowanie, POST+CSRF, worker |
| Poligon `2fc494ecaaa6ca5195c51f2cb4a3290b2fda0fb9`: `src/main/java/me/havooc/poligon/model/ScheduleDay.java`, `ScheduleElement.java`, `controller/AnnouncementController.java` | Plan po dniach i ogłoszenia | `information/`, odbiorcy po grupach i event scope |

Nagłówki referencji Poligon przypisują wskazany kontekst Łukaszowi Piętce (FUT 2025).
Nie przypisujemy autorstwa konkretnych plików gry na podstawie loginu właściciela;
żadnego ich kodu nie przeniesiono. Nowa implementacja importu, kont, komentarzy,
OAuth, Drive i zamknięcia wynika ze specyfikacji, nie z kopiowania referencji.

Jedyny vendored komponent frontendowy to **SheetJS CE 0.20.3**, autor SheetJS LLC,
Apache-2.0. `static/vendor/xlsx-0.20.3.min.js` jest pełnym niezmienionym bundlem;
notice w nagłówku i `SHEETJS-LICENSE.txt` zachowano. Źródło dystrybucji:
https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js .
SHA-256: `cc015130aa8521e7f088f88898eba949ccdcbfb38df0bd129b44b7273c3a6f41`.
Biblioteka jest serwowana lokalnie; strona importu nie pobiera jej z CDN.

Zależności Pythona są przypięte w `requirements*.txt`, instalowane przez pip
z oryginalnymi metadanymi i licencjami, bez kopiowania ich źródeł do modułów
aplikacji. Przed redystrybucją obrazu zachowaj notices z dystrybucji zależności.
Wybór licencji całej nowej aplikacji pozostaje decyzją właściciela.
