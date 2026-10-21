# Warunki rozpoczęcia PoC — appka eventowa

**Status:** lista do zatwierdzenia; samo istnienie tego dokumentu nie zezwala na uruchomienie systemu ani produkcyjnego deploymentu.

## Cel

Zbudować **jeden produkt webowy obsługujący kilka niezależnych wydarzeń jednocześnie**, z komunikatami/informacjami i mechaniką fotograficzną typu BeReal. Powiadomienia push nie są wymagane w pierwszym PoC. Pozostałe funkcje i role muszą zostać zatwierdzone w [wymaganiach](requirements.md).

## Blokery przed pracą z prawdziwymi danymi lub udostępnieniem PoC użytkownikom

- [ ] Wyznaczony właściciel produktu i techniczny reviewer potwierdzili MVP oraz zasady dostępu.
- [ ] Wymagania opisują granice każdego wydarzenia: identyfikator eventu, role, separację danych, izolację sesji i wszystkich odczytów/zapisów (włącznie ze zdjęciami i kanałami realtime).
- [ ] Wymagania zawierają test negatywny: konto z wydarzenia A nie czyta, nie zmienia i nie otrzymuje komunikatów ani zdjęć wydarzenia B.
- [ ] Backend sprawdza autoryzację operacji/obiektu. Nie przenosimy publicznego `GET /**`, globalnego WebSocket, dowolnych `isSuperAdmin` ani globalnego schematu bez `event_id`.
- [ ] Polityka zdjęć opisuje ich dostęp, zgodę, usuwanie/retencję (roboczo 30 dni po zakończeniu eventu — do potwierdzenia) i brak cache zdjęć uczestników w publicznym Service Workerze.
- [ ] Właściciele ustalili prawa do źródeł (Poligon, SSPWPhotoTaskGame, PWGame). Bez zgody kopiowania kodu tworzymy niezależną implementację opisanych zachowań.
- [ ] Dokonano przeglądu potencjalnych sekretów w repo/historii, obrazach, logach i hostingach referencji, potwierdzono ewentualną rotację aktywnych ujawnionych poświadczeń. Nie publikujemy ich wartości.
- [ ] Zatwierdzono środowisko testowe z danymi **wyłącznie syntetycznymi** i bez żadnej ścieżki automatycznego wdrożenia produkcyjnego.
- [ ] Zatwierdzono sposób code review dla `main`, minimalne uprawnienia repo/Actions oraz obsługę PR z forków (ustawienia wymagają weryfikacji przez Ownera).

## Co może rozpocząć się wcześniej

Dopuszczalny jest **projektowy spike offline**: opis kontraktów, prototyp interfejsu na danych fikcyjnych i testy izolacji jako pseudokod/specyfikacja, bez kopiowania materiałów z niejasnymi prawami i bez publikowania danych.

## Pierwsze testy PoC

1. Dwa niezależne eventy działają równolegle w jednej aplikacji.
2. Użytkownik eventu A nie widzi i nie może modyfikować zasobów eventu B (negatywne testy API, WebSocket i zdjęć).
3. Komunikaty i informacje są przypisane do właściwego eventu.
4. Zdjęcia mają kontrolę dostępu i mechanizm retencji; cache przeglądarki nie przechowuje ich bez świadomej decyzji.
5. Logowanie i walidacja ról nie dopuszczają samodzielnego nadania sobie uprawnień administracyjnych.
6. Przebieg testów nie dotyka produkcyjnego Azure ani sekretów realnych wydarzeń.

Pełny rejestr: [przegląd bezpieczeństwa 2026-10-21](reviews/2026-10-21-security-review.md).
