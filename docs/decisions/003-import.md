# ADR-003 — import

Status: zaakceptowane do lokalnego PoC (23.10.2026).

## 6. Import Excela — ADR-003

Obsługujemy standardowy .xlsx z eksportu Forms. Nie obiecujemy dowolnej zgodności z makrami, plikami szyfrowanymi, XLS i skomplikowanymi workbookami. Parser dobierz spośród utrzymywanych bibliotek z właściwą licencją; nie instaluj bezrefleksyjnie starej paczki o znajomej nazwie.

1. Przeglądarka otwiera plik lokalnie. Organizator wybiera arkusz, wiersz nagłówków, kolumnę imienia oraz opcjonalnie kolumnę grupy. Jeżeli jest tylko pełne imię i nazwisko, wymagaj przygotowania osobnej kolumny imienia; nie wysyłaj pełnego nazwiska na serwer i nie zgaduj automatycznie jego granic.
2. Podgląd pokazuje liczbę kont, puste imiona i mapowanie grup. Jednakowe imiona są dozwolone. Nie wysyłamy źródłowych komórek, numerów PESEL, maili ani skrótów tych wartości.
3. Browser tworzy losowy batch_id, techniczne UUID wierszy, losowe loginy i hasła przez Web Crypto (co najmniej 128 bitów losowości na hasło). Trzyma je wyłącznie w pamięci bieżącej karty. API otrzymuje tylko allowlistę: row_id, imię, group_ids, login, initial_password. Hasło przechodzi przez HTTPS i jest natychmiast hashowane przez Django; nie zapisujemy jawnego hasła w bazie, logach, kolejce ani cache.
4. Serwer w jednej transakcji tworzy batch i konta; waliduje wszystkie grupy i event. Klucz (event,batch_id,row_id) zapewnia idempotencję. Retry tego samego batcha nie resetuje haseł i nie tworzy nowych kont. Niezgodny payload istniejącego batcha zwraca konflikt. Odpowiedź nie zawiera haseł.
5. Po sukcesie browser zapisuje nowy .xlsx z zachowaniem wartości, kolejności wierszy i arkuszy oraz dodaniem login/hasło na końcu wybranego arkusza. Nie gwarantujemy identycznego bajtowo pliku i wszystkich zaawansowanych stylów Excela. To standardowy eksport Forms, nie uniwersalny edytor Office. Wartości wyglądające jak formuły pozostają tekstem i nie tworzymy nowych aktywnych formuł. Testuj PESEL z zerem wiodącym i długie identyfikatory.
6. Po utracie odpowiedzi ta sama karta może ponowić batch i pobrać wynik, bo ma hasła w pamięci. Po zamknięciu karty bez pobrania wyniku konieczny jest reset odpowiednich kont. Nie odzyskuj haseł z serwera. Pokaż to przed zatwierdzeniem.

Reimport wynikowego pliku: istniejące loginy przyporządkowujemy tylko we własnym evencie; puste loginy oznaczają nowe osoby, nieznane/obce loginy są błędem. Nie nadpisujemy haseł istniejących kont ani nie udajemy, że dawna kolumna hasło nadal jest aktualna. Reimport pierwotnego pliku bez loginów może utworzyć duplikaty: wyraźny podgląd i ostrzeżenie, bez deduplikacji po imieniu. Import nie służy do masowego aktualizowania istniejących osób; grupy edytuje się w panelu.

Wyeksportowany plik nadal zawiera oryginalne dane organizatora i jawne dostępy; aplikacja go nie archiwizuje. Test przeglądarkowy ma dowieść, że zbędne kolumny nie występują w żadnym żądaniu sieciowym.

