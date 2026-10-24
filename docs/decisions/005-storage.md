# ADR-005 — storage

Status: zaakceptowane do lokalnego PoC (23.10.2026).

## 9. Zdjęcia i Google Drive — ADR-005

Pierwsza integracja: własny My Drive organizatora, folder tworzony przez aplikację. Nie implementujemy arbitralnego shared link jako uprawnienia do zapisu, Google Shared Drives ani konta serwisowego jako obejścia OAuth. Uczestnik nie łączy własnego Google.

Organizator łączy konto przez OAuth authorization-code flow ze scope drive.file, state jednorazowym i powiązaniem sesji, organizatora oraz wydarzenia. Tokeny dostępne wyłącznie backendowi, szyfrowane kluczem spoza bazy/Git, redagowane w błędach. Callback na jednym skonfigurowanym hoście platformy: jednorazowy stan łączy go z wyjściowym eventem, powrót tylko do hosta z allowlisty. Nie polegaj na cookie innej subdomeny ani na dowolnym next URL. Zgoda Google może obejmować pliki aplikacji z więcej niż jednego eventu tego właściciela, więc drive.file nie zastępuje izolacji w backendzie.

Na start jeden folder i połączenie eventowe, bez zmiany właściciela magazynu w trakcie gry. Ponowne połączenie musi odtworzyć dostęp do dotychczasowego folderu. Folder prywatny podczas gry. Link do folderu widoczny organizatorowi; uczestnicy pobierają zdjęcia przez backend po autoryzacji, nie bezpośrednio przez publiczne URL-e Drive.

Pipeline:

1. Request sprawdza event, rolę, przydział, termin, expected_version, idempotency_key oraz rezerwuje operację i budżet miejsca.
2. Odbiera obraz do prywatnego pliku tymczasowego; limit wejścia 15 MiB i 40 megapikseli. Walidacja rzeczywistego formatu, nie samego rozszerzenia. Obsługuj JPEG/PNG/WebP; HEIC poza pierwszym PoC z komunikatem o konieczności konwersji. Sprawdź upload z aparatu Android/iPhone; nie deklaruj wsparcia wszystkich formatów telefonu.
3. Pillow: popraw orientację, usuń EXIF/metadane lokalizacyjne, zmniejsz dłuższy bok do 1920 px, zapisz JPEG maks. 1 MiB, obniżając jakość/rozmiar w razie potrzeby. To nowe limity projektowe, a nie istniejąca gwarancja referencji.
4. Adapter zapisuje na Drive pod losową nazwą bez imienia/loginu. Status READY dopiero po potwierdzeniu dostawcy. Id operacji przechowuj także w appProperties; po timeout najpierw szukaj rezultatu tej operacji, nie twórz ślepo następnej kopii.
5. Krótka transakcja finalizacji sprawdza ponownie status eventu, czas i wersję. Jeżeli zamknięcie/konflikt wygrał, nie publikuj zdjęcia, zaplanuj usunięcie osieroconego pliku. Jeśli commit się udał, pokaż sukces i zwolnij miejsce aktywnego zadania.
6. W finally usuń plik tymczasowy; po awarii procesu worker usuwa pliki starsze niż 1 godzinę. Retry po utracie wejściowego pliku może wymagać ponownego wyboru zdjęcia przez użytkownika. Nie twórz trwałej kolejki binarnych uploadów w bazie.

Adapter ma kontrakt create_event_folder, upload(operation_id), find_by_operation, read(file_id), delete(file_id), check_access. Przy delete 404 traktuj jako osiągnięty cel. Backend przyjmuje ID zdjęcia aplikacji, nigdy dowolny file_id od użytkownika. Download korzysta z autoryzowanego files.get alt=media. Dla galerii generuj miniatury w ograniczonym prywatnym cache; TTL maks. godzina i globalny limit 256 MiB dla PoC. Oryginały tylko strumieniowo. Nagłówki dla prywatnej treści: Cache-Control: private, no-store. Cache usuwaj natychmiast przy moderacji/podmianie/zamknięciu; klucz zawiera event i wersję zdjęcia.

Usunięcie przez organizatora: potwierdzenie w UI, POST z CSRF, natychmiastowe ukrycie i usunięcie ocen/komentarzy; kolejka usuwa tylko ten plik utworzony przez aplikację. W PoC to trwałe usunięcie przez API, nie przeniesienie do kosza. Panel pokazuje pending/failed i możliwość ponowienia; nie udaje, że plik zniknął, jeżeli Google odmówił. Awaria dysku nie blokuje aktualności i harmonogramu, ale blokuje nowe skuteczne zgłoszenia.

Domyślny budżet zapisanych zdjęć wydarzenia: 2 GiB, konfigurowalny przez organizatora w granicach ustawień platformy. Budżet obejmuje pending reservations i nieusunięte stare pliki, nie tylko widoczną galerię; nie zastępuje rzeczywistego limitu konta Google. Przekroczenie zwraca zrozumiały błąd bez zaliczenia zadania. Worker zwalnia rezerwacje po rozstrzygnięciu operacji. Przykład: 200 osób × 50 zadań × 1 MiB ≈ 9,8 GiB; pięć aktywnych zadań nie ogranicza liczby wszystkich zdjęć do 1000. Nie obiecuj, że każde wydarzenie zmieści się w darmowym koncie.

Lokalny FakeStorage realizuje ten sam kontrakt w prywatnym katalogu, obsługuje symulowane timeouty/brak miejsca/odmowę. Wolno go używać tylko w development/tests; konfiguracja produkcyjna musi odmówić startu z takim adapterem. PoC ma zawierać prawdziwy adapter Drive i instrukcję OAuth, nawet gdy live test jest jeszcze niewykonany.

