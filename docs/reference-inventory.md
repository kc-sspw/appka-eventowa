# Referencje i katalog kandydatów do adaptacji

**Stan statycznego odczytu: 23.10.2026.** To mapa miejsc, które warto obejrzeć podczas planowania PoC, **nie** wybór technologii ani zobowiązanie do przeniesienia komponentów. Nazwy plików pochodzą z rzeczywistych repozytoriów na `main`. Zastosowanie jest **hipotezą do oceny po opisie użytkownika**.

## 1. Poligon — `kc-sspw/apka-wyjazdowa`

| Obszar do porównania z wymaganiami | Znalezione pliki | Co można ocenić / ryzyko |
|---|---|---|
| Harmonogram | `src/main/java/me/havooc/poligon/controller/ScheduleController.java`, `model/ScheduleDay.java`, `model/ScheduleElement.java`; `flutter/lib/service/schedule_service.dart` | Model dni i elementów; obecne grupowanie według `TrainingPath` nie zapewnia samo z siebie izolacji dowolnych równoległych wydarzeń. |
| Uczestnicy i profile | `controller/CrewController.java`, `model/Crew.java`, `flutter/lib/screen/crew_screen.dart` | Pomysły na dane i UI. **Nie kopiować** publicznego GET zwracającego całą encję i wrażliwe pola ani uprawnień opartych na polu przesłanym przez klienta. |
| Ogłoszenia | `controller/AnnouncementController.java`, `model/Announcement.java`, `flutter/lib/service/announcement_service.dart` | Przebieg publikacji. Aktualne odczyty `findAll()` i broadcast są globalne, nie per event. |
| Zadania dzienne | `controller/DailyQuestController.java`, `model/DailyQuest.java`, `flutter/lib/service/daily_service.dart` | Opcjonalna inspiracja na później; nie zakładać obecności w MVP. |
| Inne funkcje | `TeamController.java`, `TrainerController.java`, `SongController.java`, `SmsController.java` | Mogą być zbędne; najpierw ustalić wymagania. SMSAPI nie jest domyślną zależnością nowej appki. |
| Login | `security/FirebaseAuthenticationFilter.java`, `security/SecurityConfig.java`, `service/VerifiedUsersService.java` | Analiza istniejącego rozwiązania. Sam token/allowlista to za mało do RBAC per event; `SecurityConfig` dopuszcza wszystkie GET. Nie kopiować konfiguracji 1:1. |
| Aktualizacje realtime | `security/WebSocketConfig.java`, `security/WebSocketHandler.java` | Do rozważenia dopiero jeśli potrzebne. Obecny handler rozsyła wiadomości globalnie i dopuszcza wszystkie origins — wymagana przebudowa autoryzacji i kanałów per event. |
| Klient Flutter | `flutter/lib/` | Inspiracja przebiegami/interfejsem. Flutter nie jest automatycznym wyborem dla planowanego produktu webowego. |

## 2. Gra fotograficzna — `Korniszon99/SSPWPhotoTaskGame`

| Obszar | Gdzie zacząć | Ocena |
|---|---|---|
| Zadania i losowanie | `photo_game/database/schema.sql`, pliki `photo_game/` i `README.md` | Znany przepływ: zadanie → przypisanie użytkownikowi → wykonanie ze zdjęciem. Zakres adaptacji zależy od wizji właściciela. |
| Zdjęcia, galerie i oceny | `photo_game/database/schema.sql`, `photo_game/js/ratings.js` | Schemat zawiera `completed_tasks` i `photo_ratings` z `UNIQUE(photo_id,user_id)`. **Brak `event_id`** w obecnym schemacie; nie importować globalnego modelu jako systemu wieloeventowego. |
| Logowanie / administracja | `photo_game/auth/login.php`, `auth/register.php`, `config/config.php` | Ocenić UX i już zastosowane zabezpieczenia, ale dostosować do ról i scope wydarzenia. |
| PWA / cache | `photo_game/sw.js`, `photo_game/js/pwa.js` | Referencyjny `main` nadal ma strategię cache-first dla obrazów; w [osobnym PR](https://github.com/Korniszon99/SSPWPhotoTaskGame/pull/4) przygotowano poprawkę, ale **nie jest scalona** w momencie odczytu. W nowej aplikacji nie cache'ować zdjęć uczestników domyślnie. |
| Rankingi | `README.md`, `photo_game/database/schema.sql` | Funkcja istnieje w referencji, ale **nie jest automatycznie funkcją nowego PoC**. |

Starszy [PWGame](https://github.com/Korniszon99/PWGame) może służyć wyłącznie jako dodatkowe źródło pomysłów. Nie kopiujemy domyślnych haseł, kodów dostępu ani procedur inicjalizacji historycznych kont.

## 3. Zasady przenoszenia kodu

Użytkownik potwierdził prawo do wykorzystania kodu referencyjnego (23.10.2026). Prawa do kodu nie przesądzają, które fragmenty będą sensownie kompatybilne ani czy zależności trzecie można bez zmian redystrybuować. Przy konkretnym reuse zapisuj: `source repo + commit + path + autorzy + zakres modyfikacji + wymagane informacje o licencji`. Unikaj całkowitego kopiowania projektu i przypadkowego importowania historii/sektorów produkcyjnych.

**Do niezależnego zaprojektowania w PoC:** event jako główny kontekst uprawnień, egzekwowanie RBAC per event, zakres danych każdej operacji, separacja plików i kanałów realtime, bezpieczne przechowywanie zdjęć i ich retencja.

## 4. Co zrobi chat od zakresu

Po otrzymaniu szczegółowej wizji użytkownika przygotuje tabelę:

| Przypadek użycia użytkownika | Status MVP | Źródło referencyjne / ścieżka | Reuse / rewrite / nowe / później | Uzasadnienie | Test akceptacyjny |
|---|---|---|---|---|---|
| *Wypełnić po decyzjach* | | | | | |

Bez zatwierdzonego opisu nie tworzymy listy funkcji tylko na podstawie referencji.

**Uwaga:** [przegląd bezpieczeństwa z 21.10.2026](reviews/2026-10-21-security-review.md) jest historyczną analizą wybranych wersji źródeł. Nie dowodzi, że wszystkie wskazane problemy nadal istnieją; przed skopiowaniem plików zawsze sprawdź bieżące `main`.
