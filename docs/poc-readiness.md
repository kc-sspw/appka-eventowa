# Warunki PoC — appka eventowa

**Stan na 23.10.2026:** repo publiczne i chronione, referencje zidentyfikowane, prawa do adaptacji potwierdzone przez właściciela. **Można rozpocząć planowanie i lokalne prace na danych syntetycznych.** Nie oznacza to zgody na udostępnienie aplikacji rzeczywistym uczestnikom ani wdrożenie.

## Dwa różne progi gotowości

### A. Rozpoczęcie rozmowy o zakresie i lokalnego PoC

- [x] Główne repo produktu to `kc-sspw/appka-eventowa`; Poligon i gra fotograficzna są **referencjami**, nie gotowym produktem.
- [x] Właściciel potwierdził prawo do korzystania z kodu referencyjnego (z zachowaniem atrybucji i analizy zależności).
- [x] GitHub: repo `public`, gałąź `main` objęta aktywnym Rulesetem: PR, jedna akceptacja, ochrona przed force-push i usunięciem, Owner PR-only bypass.
- [x] Zdefiniowano granice bezpieczeństwa: tylko dane syntetyczne, brak sekretów i prawdziwych zdjęć, brak produkcyjnego deploymentu z repo.
- [ ] Właściciel opisał szczegółową wizję, role, funkcje i pierwsze scenariusze PoC.
- [ ] Zatwierdzono minimalny zakres pierwszego pionowego wycinka i zakres elementów adaptowanych z referencji.
- [ ] Uzgodniono technologię, sposób uruchomienia lokalnego i pierwszy ADR.

Wymagania i wybór technologii są **celowo otwarte** do następnego chatu: [POC_START_HERE.md](POC_START_HERE.md).

### B. Udostępnienie PoC użytkownikom / użycie rzeczywistych danych

Poniższe pozostaje **NO-GO**, dopóki nie zostanie sprawdzone i zatwierdzone:

- [ ] Właściciel produktu i reviewer zaakceptowali MVP, role i macierz uprawnień.
- [ ] Każdy obiekt, API, zapis, plik, powiadomienie i kanał realtime ma ustalony kontekst `event_id` oraz autoryzację po stronie backendu.
- [ ] Test negatywny: konto wydarzenia A nie czyta, nie zmienia i nie otrzymuje treści ani zdjęć wydarzenia B; test obejmuje także zgadywanie identyfikatorów obiektów.
- [ ] Nie przeniesiono publicznego `GET /**`, globalnego WebSocket broadcast ani możliwości ustawiania `isSuperAdmin` w danych wejściowych klienta z Poligonu.
- [ ] Zatwierdzono politykę zdjęć (zgody, widoczność, uprawnienia, usuwanie/retencja). **30 dni po zakończeniu wydarzenia** to nadal wartość robocza.
- [ ] Przeprowadzono weryfikację aktywnych sekretów, logów i danych **środowiska docelowego**. Historyczne poświadczenia Poligonu zostały przez właściciela opisane jako testowe i nie stanowią blokera projektowego; nie kopiować ich do nowego systemu.
- [ ] Zweryfikowano autoryzację, bezpieczeństwo przesyłania plików, kontrolę dostępu do zdjęć oraz brak publicznego cache uploadów.
- [ ] Wykonano testy integracyjne i bezpieczeństwa odpowiednie do użytych zależności; sam statyczny audyt nie wystarcza.
- [ ] Zatwierdzono oddzielne środowisko pilotażu, role osób obsługujących wdrożenie, retencję i postępowanie przy incydencie. Produkcyjne CI pozostaje poza GitHub Actions.
- [ ] Sprawdzono rzeczywiste uprawnienia Teams, pozaorganizacyjnych współpracowników oraz polityki Actions/fork PR. Sam Ruleset nie stanowi całej kontroli dostępu.

## Minimalne scenariusze testowe lokalnego PoC

1. Dwa eventy istnieją i są obsługiwane jednocześnie.
2. Użytkownik eventu A **nie może** uzyskać treści/zdjęć/komunikatów eventu B ani zmienić ich przez API, podmianę ID, websocket czy bezpośredni URL do pliku.
3. Konto bez wymaganej roli nie może edytować danych eventu ani przyznać sobie roli administracyjnej.
4. Jeśli w PoC są zdjęcia, są dostępne wyłącznie osobom uprawnionym; nie są przechowywane w publicznym PWA cache.
5. Włączone przypadki użycia dają się uruchomić na syntetycznych danych, na jednej instrukcji lokalnego startu.
6. Testy nie dotykają Azure Production, rzeczywistych sekretów ani kont SSPW.

**Uwaga:** to testy bazowe. Ostateczna lista zależy od zaakceptowanych funkcji PoC. Obecne repo zawiera dokumentację i **nie przeprowadzono testów kodu aplikacji**, ponieważ aplikacja jeszcze nie powstała.

Tło i granice wnioskowania: [statyczny przegląd 21.10](reviews/2026-10-21-security-review.md). Zasady reuse: [source-provenance.md](source-provenance.md).
