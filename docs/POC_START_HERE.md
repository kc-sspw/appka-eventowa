# Aktualny punkt startu — 24.10.2026

Zakres jest już zatwierdzony, a implementacja PoC znajduje się na gałęzi `feat/django-event-poc`. Zacznij od [README](../README.md), [wymagań](requirements.md), [raportu testów](testing.md) i [instrukcji organizatora](organizer-guide.md). Poniższe przekazanie z 23.10 jest historycznym opisem etapu sprzed specyfikacji; nie otwiera ponownie zamkniętych decyzji.

---

# PoC — instrukcja dla kolejnego chatu

**Stan wejściowy: 23.10.2026.** Ten dokument przygotowuje **rozmowę o zakresie i architekturze PoC**, a nie stanowi zatwierdzonej specyfikacji implementacji.

## 1. Punkt odniesienia

- **Główne repo produktu:** [kc-sspw/appka-eventowa](https://github.com/kc-sspw/appka-eventowa). Jest publiczne; `main` ma aktywny repozytoryjny Ruleset.
- **Referencja Poligon:** [kc-sspw/apka-wyjazdowa](https://github.com/kc-sspw/apka-wyjazdowa) — backend Spring Boot, Flutter, ekipa/uczestnicy, harmonogram, ogłoszenia, zadania, WebSocket. **Nie** jest bazą produkcyjną z zatwierdzoną architekturą.
- **Referencja gry fotograficznej:** [Korniszon99/SSPWPhotoTaskGame](https://github.com/Korniszon99/SSPWPhotoTaskGame) — PHP/PWA, zadania zdjęciowe, przesyłanie zdjęć, oceny, ranking, panel administratora.
- **Referencja starsza:** [Korniszon99/PWGame](https://github.com/Korniszon99/PWGame) — wyłącznie jako dodatkowy kontekst; nie przenosić historycznych domyślnych loginów/kodów.
- **Prawa do użycia kodu:** użytkownik potwierdził 23.10.2026, że prawa do wykorzystania kodu są zapewnione. Zachowuj oznaczenia autorów, weryfikuj pochodzenie faktycznie kopiowanych plików i zależności/licencje zewnętrzne. Mechanika „typu BeReal” **nie oznacza** prawa do kodu, logo lub marki firmy BeReal.
- **Poświadczenia historyczne Poligonu:** według użytkownika były testowe, nie jego, i nie są blokadą startu projektowego PoC. Nigdy nie przenoś ich do nowego repo. Nadal obowiązuje brak prawdziwych sekretów w Git.

## 2. Co jest znane, a co czeka na opis właściciela

**Znane z dotychczasowych wymagań:** jedna aplikacja webowa obsługująca wiele niezależnych wydarzeń/wyjazdów jednocześnie; role, harmonogram, uczestnicy, zdjęcia i informacje/komunikaty przypisane do konkretnego wydarzenia. Rozważana jest mechanika fotograficzna podobna do BeReal. Robocza retencja zdjęć: 30 dni po zakończeniu wydarzenia; powiadomienia push nie są wymagane dla pierwszego PoC. Większość szczegółów nie jest jeszcze zatwierdzona.

**W kolejnym czacie właściciel opisze po swojemu, szczegółowo i heurystycznie, jak produkt ma działać.** Nie nadpisuj tego opisu gotową listą funkcji z Poligonu. W szczególności **nie wybieraj stacku, schematu bazy, listy ekranów, dostawcy logowania, hostingu ani podziału MVP** przed przeanalizowaniem nowego opisu.

## 3. Kolejność pracy w czacie o zakresie

1. Przyjmij cały opis właściciela i ułóż go w **scenariusze użytkowników, role/uprawnienia, dane, ekrany, procesy, integracje i wyjątki**; odróżnij ustalenia od propozycji.
2. Wskaż sprzeczności, ukryte założenia i braki wpływające na architekturę. Pytaj tylko o decyzje konieczne do implementacji; rzeczy niekrytyczne oznacz jako świadome założenia.
3. Porównaj wymagania z konkretnymi modułami obu referencji, opierając się na aktualnym kodzie repo, a nie tylko nazwach technologii. Dla każdej funkcji wskaż: **adaptować fragment / przepisanie bezpiecznej logiki / nowa implementacja / odroczyć**, z uzasadnieniem i lokalizacją plików.
4. Zaproponuj najmniejszy działający **pionowy wycinek PoC**, a nie tylko niezależne ekrany: tworzenie/selekcja wydarzenia → uprawniony udział → co najmniej jedna kompletna interakcja użytkownika → zapis i odczyt → izolacja danych dwóch wydarzeń.
5. Dopiero po zatwierdzeniu zakresu dobierz **technologie, moduły, kontrakt API, model danych i testy**. Nie kopiuj całego backendu Poligonu ani globalnego schematu gry fotograficznej.
6. Zapisz wynik w `docs/requirements.md`, ADR-ach w `docs/decisions/` i krótkim planie implementacji (kolejność PR-ów, definition of done), a następnie przygotuj **jeden samowystarczalny prompt dla osobnego chatu implementacyjnego**. Uwzględnij źródła i gałąź docelową.
7. Jeżeli kolejny chat ma bezpośrednio implementować, najpierw wykonaj kroki 1–5 i uzgodnij minimalny zakres, zamiast bez uzasadnienia tworzyć rozbudowany scaffold.

## 4. Granice techniczne, niezależne od wyboru stacku

- **Izolacja danych per event po stronie serwera**: każde zapytanie, operacja zapisu, zdjęcie, kanał realtime, komunikat i relacja użytkownik–event sprawdza uprawnienia i kontekst wydarzenia. Użytkownik A nie uzyskuje danych wydarzenia B przez zmianę ID w URL lub body.
- **Autoryzacja operacji**: nie wystarczy Firebase ID token lub samo zalogowanie; role i możliwość edycji muszą być egzekwowane w backendzie. Nie pozwalaj klientowi deklarować sobie administratora.
- **Prywatność plików**: żadne uploady zdjęć ani dane uczestników nie są publikowane w repo, globalnym katalogu statycznym lub niekontrolowanym PWA cache. Przy dostępie do pliku też sprawdzaj membership wydarzenia.
- **Retencja i zgody**: mechanizm 30 dni to hipoteza produktowa, która wymaga zatwierdzenia i testu; dla lokalnego PoC można ją konfigurować na danych syntetycznych.
- **Wdrożenie**: repo GitHub służy kodowi i PR-om; za przyszłe wdrożenia produkcyjne odpowiada oddzielna infrastruktura CI. Nie dodawaj automatycznego deploymentu przez GitHub Actions. Lokalny development i izolowane testy są dozwolone.
- **Dane**: wyłącznie syntetyczne dane/seedy i pliki w PoC; sekrety wyłącznie w niezacommitowanym środowisku. Żadnych baz produkcyjnych ani prywatnych zasobów SSPW.
- **Review**: gałęzie robocze i PR-y do `main`; Ruleset wymaga akceptacji (Owner ma PR-only bypass). Nie wykonuj force-pusha ani bezpośredniego commita na `main`.

Zobacz też [warunki PoC](poc-readiness.md), [statyczny audyt referencji](reviews/2026-10-21-security-review.md), [inwentarz modułów](reference-inventory.md) oraz [pochodzenie kodu](source-provenance.md).

## 5. Wymagany rezultat rozmowy o zakresie

- Wersjonowana, zaakceptowana lista **MUST / SHOULD / LATER / OUT** z kryteriami odbioru.
- Mapa ról i uprawnień, w tym przypadki odmowy.
- Scenariusz co najmniej dwóch równoległych eventów (wraz z negatywnymi testami przecieków danych).
- Rozdział funkcji adaptowanych z Poligonu i gry fotograficznej oraz elementów nowych.
- Wybór architektury z krótkim ADR i diagramem odpowiedzialności.
- Testowalny PoC lokalny: instrukcja startu, syntetyczne konta/dane, testy, znane ograniczenia.
- Samowystarczalny prompt wykonawczy do nowego chatu: repo/branch, zakres, źródła, krok po kroku, zakazy i definition of done.

**Nie deklaruj gotowości do pilotażu z realnymi uczestnikami wyłącznie dlatego, że lokalny PoC działa.** Kryteria publicznego pilotażu ustala osobno właściciel produktu.

## 6. Prompt do skopiowania jako pierwsza wiadomość w kolejnym czacie

> Pracujemy nad PoC aplikacji eventowej Komisji Cyfryzacji SSPW. Główne repo: https://github.com/kc-sspw/appka-eventowa . Na początek odczytaj README, `docs/POC_START_HERE.md`, `docs/requirements.md`, `docs/reference-inventory.md`, `docs/poc-readiness.md` oraz `docs/source-provenance.md`. Referencje: https://github.com/kc-sspw/apka-wyjazdowa (Poligon) i https://github.com/Korniszon99/SSPWPhotoTaskGame (gra fotograficzna). Nie zakładaj, że ich technologie ani wszystkie funkcje muszą być przejęte.
>
> Za chwilę podam bardzo szczegółowy opis swojej wizji aplikacji, jej zachowania i przepływów. Najpierw pomóż mi zamknąć zakres i architekturę; rozdziel to, co jest moją decyzją, od Twoich sugestii. Na podstawie faktycznych plików referencyjnych dobierz elementy do adaptacji, nie kopiując wprost niezabezpieczonych mechanizmów. Dopiero po uzgodnieniu zakresu i ADR przygotuj samowystarczalny prompt dla oddzielnego chatu, który zaimplementuje pierwszą wersję aplikacji. Nie rozpoczynaj teraz wdrożenia, nie twórz GitHub Actions deploymentu i nie stosuj rzeczywistych danych/poświadczeń. Pracujemy na osobnych branchach i przez PR, z zachowaniem Rulesetu.

