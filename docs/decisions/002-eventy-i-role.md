# ADR-002 — eventy-i-role

Status: zaakceptowane do lokalnego PoC (23.10.2026).

## 5. Eventy, konta i uprawnienia — ADR-002

Event rozpoznajemy wyłącznie z zatwierdzonego hosta/subdomeny, np. event-a.events.example.org. Nie ufamy event_id z formularza, query string ani dowolnemu X-Forwarded-Host. W produkcji jedna konfiguracja wildcard DNS/TLS kieruje ruch do aplikacji; utworzenie eventu dodaje rekord, nie osobny deployment. Domena i infrastruktura pozostają parametrami wdrożenia. Lokalnie dwa hosty w hosts/konfiguracji proxy, bez zależności od publicznego DNS.

Sesja cookie host-only, HttpOnly, SameSite=Lax, Secure przy HTTPS. Brak wspólnego SESSION_COOKIE_DOMAIN dla eventów. Każdy odczyt, zapis, download i zadanie workera weryfikuje kontekst eventu; UUID nie zastępuje uprawnień. Nieznany slug odrzucamy. Dla wyczyszczonego wydarzenia pokazujemy neutralne 410 bez danych, nawet jeśli wildcard DNS nadal je obsługuje. Nie przydzielamy starego slugu nowemu wydarzeniu.

Najprostszy model PoC: eventowe konta organizatorów i uczestników oraz oddzielne konta administratorów platformy. Ta sama osoba obsługująca dwa wydarzenia może dostać dwa konta organizatora. Login wewnętrzny globalnie losowy/unikalny, ale logowanie wymaga właściwego eventu. Imię nie jest identyfikatorem. Brak obowiązkowych maili/telefonów. Organizator ma is_staff=false; rola jest nadawana przez administratora platformy, nigdy przez publiczny formularz.

| Operacja | Uczestnik | Organizator wydarzenia | Administrator platformy |
|---|---|---|---|
| Tworzenie eventu i nadawanie organizatorów | Nie | Nie | Tak |
| Import/ręczne konta/reset uczestnika | Nie | Własny event | Wyłącznie jawna pomoc administracyjna |
| Grupy, publikacje, harmonogram, pula i start gry | Odczyt dostępnych treści | Własny event | Pomoc administracyjna |
| Podłączenie dysku i zamknięcie eventu | Nie | Własny event | Tak |
| Losowanie i zdjęcie | Własne przydziały | Podgląd/moderacja; test gry przez osobne konto testowe | Brak automatycznej roli gracza |
| Galeria i komentarze | Własny event | Własny event | Brak domyślnej galerii wszystkich eventów |
| Ocena uczestnika | Cudze zdjęcie, 1–5 | Nie | Nie |
| Ocena organizatora | Nie | 0–5 we własnym evencie | Nie domyślnie |
| Usuwanie zdjęć i komentarzy | Własny komentarz | Własny event | Jawna interwencja administracyjna |

Uprawnienia platformowe są technicznie uprzywilejowane, ale nie powinny przypadkowo omijać event scope w zwykłym widoku. Obce ID zwracają 404, brak uprawnień do operacji we własnym evencie 403. Nie przekazuj klientowi hashy haseł, tokenów, sekretów ani całych encji użytkownika. Reset hasła unieważnia wcześniejsze sesje konta. Limit prób logowania i uploadów egzekwuj na serwerze.

