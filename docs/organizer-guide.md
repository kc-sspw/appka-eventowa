# Instrukcja organizatora

## Dostęp i przygotowanie

Operator platformy tworzy wydarzenie i konto organizatora. Otrzymasz jego adres
oraz losowy login i hasło. Używaj adresu swojego wydarzenia, nie panelu platformy.
Po zalogowaniu otwiera się **Panel organizatora**.

1. W **Ustawieniach** wpisz nazwę, daty wydarzenia, termin gry, instrukcję oraz
   budżet zdjęć w MiB. Godziny formularzy dotyczą Warszawy. Gra musi mieścić się
   wewnątrz wydarzenia; koniec gry może być wcześniejszy niż zamknięcie aplikacji.
2. W **Grupach** dodaj grupy odbiorców. Jedna osoba może należeć do kilku grup.
3. W **Puli zadań** utwórz zadania. Po pierwszym przydziale treści nie można
   zmienić; wadliwe zadanie wycofaj i dodaj nowe. Niewykonane przydziały zostaną
   anulowane, a wykonane zdjęcia pozostaną.
4. Podłącz magazyn, przygotuj treści i konta. Dla testowego lokalnego wydarzenia
   wybierz **Przygotuj lokalny magazyn**; seedy mają go już gotowego.
5. **Aktywuj wydarzenie**. Uczestnicy nie mają dostępu do treści w stanie
   Przygotowanie. Losowanie i upload są dodatkowo ograniczone terminem gry.

## Uczestnicy i XLSX

Możesz dodać osobę ręcznie w **Uczestnicy → Dodaj uczestnika**. Ekran pokazuje
nowe hasło jednorazowo. Aplikacja nie wysyła maili ani SMS.

Dla eksportu Forms:

1. Przygotuj standardowy `.xlsx`, maks. 10 MiB; do 500 importowanych osób.
   Potrzebna jest kolumna **samego imienia**. Przy imieniu i nazwisku w jednej
   kolumnie przygotuj osobną kolumnę imienia przed importem.
2. W **Importuj XLSX** wybierz plik, arkusz, wiersz nagłówków, kolumnę imienia
   i opcjonalnie grupy. Arkusz pozostaje w pamięci bieżącej karty.
3. Potwierdź, że kolumna zawiera samo imię, i wybierz **Przygotuj podgląd**.
   Uzupełnij puste imiona. Każdą etykietę grupy z arkusza przypisz do jednej lub
   kilku istniejących grup wydarzenia. Powtarzające się imiona są dozwolone.
4. Potwierdź zasady i wybierz **Utwórz konta**, następnie **Pobierz XLSX z dostępami**.
   Zapisz plik przed zamknięciem karty. Zawiera oryginalne dane i jawne hasła;
   przekaż dostępy własnym uzgodnionym kanałem i przechowuj plik bezpiecznie.

Zachowujemy wartości, kolejność wierszy i arkuszy, ale nie zaawansowane style
Excela. Formuły nie są eksportowane jako aktywne formuły. Login i hasło są dodawane
na końcu wybranego arkusza. PESEL, e-mail, inne kolumny ani ich skróty nie trafiają
do serwera; serwer otrzymuje tylko imię, identyfikatory grup i dane techniczne konta.

Po problemie sieciowym użyj **Ponów ten sam import** w tej samej karcie. Operacja
nie tworzy drugiego zestawu kont. Po utracie karty hasła nie są odzyskiwalne;
znajdź konta w **Uczestnikach** i użyj resetu. Reset usuwa wcześniejsze sesje.
Przy błędzie walidacji, zanim serwer przyjął import, popraw źródło i rozpocznij
nowy import. Nie zamykaj karty przy niepewnym wyniku operacji.

Reimport pliku z kolumną `login` zachowuje istniejące konta tego wydarzenia;
nie aktualizuje imienia, grup ani hasła. Kolumna `hasło` dla istniejących kont
zostaje wyczyszczona, aby nie udawać aktualności starego hasła. Puste loginy tworzą
nowe konta. Nieznane lub obce loginy odrzucają całą operację. Reimport pierwotnego
pliku bez loginów może stworzyć duplikaty — nie deduplikujemy po imieniu.

## Treści i podgląd

**Publikacje** obsługują Aktualności i Stałe informacje. Wybierz odbiorców
Wszyscy albo Wybrane grupy; uczestnik widzi sumę swoich grup. Przypięcie nie
zamienia aktualności w stałą informację. Treść jest zwykłym bezpiecznym tekstem.
Możesz zaplanować późniejszą publikację.

**Plan ramowy**: dodaj tytuł, początek, opcjonalny koniec, miejsce, opis i grupy.
Widok porządkuje wpisy po dniach. Zakładka Informacje pojawia się dopiero, gdy
konto ma widoczną stałą informację lub pozycję planu.

Organizator widzi wszystkie swoje treści, w tym zaplanowane. Aby sprawdzić widok
konkretnej grupy lub zagrać próbnie, utwórz osobne syntetyczne konto uczestnika
z tą grupą i zaloguj się w prywatnym oknie przeglądarki. Nie ma osobnego trybu
podszywania się pod uczestnika.

## Gra i moderacja

Uczestnik ma maksymalnie pięć zadań do wykonania jednocześnie. Potwierdzone zdjęcie
zwalnia miejsce; błąd uploadu nie zalicza zadania. JPEG, PNG i WebP do 15 MiB,
40 megapikseli, bez animacji. HEIC należy przekonwertować. Aplikacja usuwa metadane,
koryguje orientację i zapisuje JPEG do 1920 px i 1 MiB.

Podmiana jest możliwa do końca gry. Stare zdjęcie pozostaje do sukcesu nowego;
potem jego oceny i komentarze są usuwane, a stary plik trafia do kolejki usunięcia.
Wycofane lub usunięte moderacyjnie zadanie nie wraca do puli.

W galerii otwórz zdjęcie. Uczestnicy oceniają cudze zdjęcia 1–5, jeden edytowalny
głos na osobę. Organizatorzy mają osobną wspólną ocenę 0–5, z oznaczeniem ostatniej
edycji. Nie ma rankingu. Autor usuwa własny komentarz; organizator może usunąć
każdy komentarz w swoim wydarzeniu.

W sekcji **Moderacja zdjęcia** potwierdź trwałe usunięcie. Zdjęcie znika od razu,
a worker usuwa plik. Panel magazynu pokazuje statusy i ponowienia. `RETRY` oznacza
brak potwierdzenia; nie oznacza sukcesu usunięcia. `NEEDS_INPUT` oznacza, że autor
musi wybrać zdjęcie ponownie. Brak miejsca lub cofnięta zgoda nie blokują informacji
i planu. Budżet uwzględnia także rezerwacje oraz pliki czekające na usunięcie.

## Google Drive i zamknięcie

Operator najpierw konfiguruje projekt Google Cloud. W panelu wybierz
**Połącz / odnów Google Drive**, zaloguj właściwe konto organizatora i zatwierdź
uprawnienia. Aplikacja tworzy własny prywatny folder. Sam link do istniejącego
folderu nie nadaje uprawnień do zapisu. Nie obsługujemy Shared Drives.

Użyj **Sprawdź dostęp i miejsce** oraz wyślij sztuczne zdjęcie z konta testowego.
Po cofnięciu zgody odnów połączenie tym samym kontem; istniejący folder zostaje.
Domyślne 2 GiB w aplikacji to budżet wydarzenia, nie gwarancja wolnego miejsca Google.

Przed zamknięciem zachowaj URL folderu i sprawdź zaległe operacje. Otwórz
**Zamknij wydarzenie**, przeczytaj skutki i wpisz slug. Dostęp uczestników znika
natychmiast. Worker usuwa konta, treści, głosy, komentarze, referencje plików,
sesje i tokeny. Przy awarii usuwania status pozostaje Porządkowanie; operator
platformy może ponowić sprzątanie. Zamknięcia nie można cofnąć.

Aktualny album pozostaje na Drive. Po zamknięciu udostępnij go samodzielnie,
najlepiej wybranym odbiorcom tylko do odczytu. Link „każdy z linkiem” można
przekazywać dalej — aplikacja nigdy nie włącza takiego dostępu automatycznie.
Po wybranym czasie, np. siedmiu dniach, usuń album samodzielnie i opróżnij kosz,
jeśli chcesz odzyskać miejsce. Aplikacja nie ma wtedy album URL ani tokenów.
