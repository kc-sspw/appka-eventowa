import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

from accounts.models import Account
from events.lifecycle import clean_event
from game.models import Photo, Task
from information.models import Entry

pytestmark = [
    pytest.mark.browser,
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        os.environ.get("RUN_BROWSER_TESTS") != "1",
        reason="Set RUN_BROWSER_TESTS=1 and install Chromium",
    ),
]


@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--host-resolver-rules=MAP *.localhost 127.0.0.1", "--no-proxy-server"]
        )
        yield browser
        browser.close()


def login(page, origin, account):
    page.goto(origin + "/auth/login")
    page.get_by_label("Login", exact=True).fill(account.username)
    page.get_by_label("Hasło", exact=True).fill("synthetic-test-password")
    page.get_by_role("button", name="Zaloguj").click()
    expect(page.get_by_role("button", name="Wyloguj")).to_be_visible()


def responsive(page, name):
    output = Path("test-results")
    output.mkdir(exist_ok=True)
    for width in [360, 390, 430, 1280]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
            f"Overflow at {width}px"
        )
        if width in [390, 1280]:
            page.screenshot(path=str(output / f"{name}-{width}.png"), full_page=True)


def test_participants_organizer_photo_flow(browser, live_server, world, jpeg):
    origin = f"http://event-a.events.localhost:{urlparse(live_server.url).port}"
    other = origin.replace("event-a", "event-b")
    Entry.objects.create(
        event=world.a, kind="NEWS", title="Witaj na wyjeździe", body="Syntetyczna informacja"
    )
    Task.objects.create(event=world.a, description="Złap syntetyczny kadr")
    contexts = [browser.new_context(viewport={"width": 390, "height": 900}) for _ in range(3)]
    pages = [context.new_page() for context in contexts]
    p1, p2, organizer = pages
    errors = []
    for page in pages:
        page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        for page, account in zip(pages, [world.p, world.peer, world.o]):
            login(page, origin, account)
        p1.goto(origin + "/game")
        p1.get_by_role("button", name="Wylosuj zadanie").click()
        expect(p1.get_by_role("heading", name="Złap syntetyczny kadr")).to_be_visible()
        file = jpeg()
        p1.locator('input[type="file"]').set_input_files(
            {"name": "generated.jpg", "mimeType": "image/jpeg", "buffer": file.read()}
        )
        p1.get_by_role("button", name="Wyślij zdjęcie").click()
        expect(p1.get_by_text("Zdjęcie potwierdzone. Zadanie wykonane!")).to_be_visible()
        photo = Photo.objects.get(event=world.a)
        p2.goto(f"{origin}/photos/{photo.pk}")
        p2.get_by_label("Twoja ocena").select_option("5")
        p2.get_by_role("button", name="Zapisz ocenę").click()
        p2.get_by_label("Twój komentarz").fill("<script>nie uruchamiaj</script>")
        p2.get_by_role("button", name="Dodaj komentarz").click()
        expect(p2.get_by_text("<script>nie uruchamiaj</script>", exact=True)).to_be_visible()
        organizer.goto(f"{origin}/photos/{photo.pk}")
        organizer.get_by_label("Wspólna ocena organizatorów").select_option("4")
        organizer.get_by_role("button", name="Zapisz ocenę").click()
        assert photo.ratings.get().value == 5
        assert photo.organizer_score.value == 4
        responsive(p2, "photo")
        p1.goto(origin + "/gallery")
        responsive(p1, "gallery")
        p1.goto(origin + "/game")
        responsive(p1, "game")
        p1.keyboard.press("Control+Home")
        p1.keyboard.press("Tab")
        assert p1.evaluate("document.activeElement !== document.body")
        p1.goto(other + "/gallery")
        expect(p1.get_by_label("Login", exact=True)).to_be_visible()
        organizer.goto(f"{origin}/photos/{photo.pk}")
        organizer.get_by_text("Moderacja zdjęcia", exact=True).click()
        organizer.get_by_label("Potwierdzam trwałe usunięcie.").check()
        organizer.get_by_role("button", name="Usuń zdjęcie", exact=True).click()
        assert not Photo.objects.filter(pk=photo.pk).exists()
        organizer.goto(origin + "/organizer/close")
        organizer.locator('input[name="confirm"]').fill("event-a")
        organizer.get_by_role("button", name="Zamknij", exact=False).click()
        clean_event(world.a.pk)
        assert p2.goto(origin + "/gallery").status == 410
        assert Account.objects.filter(event=world.b).exists()
        assert errors == []
    finally:
        for context in contexts:
            context.close()


def test_xlsx_network_allowlist_preserves_values_and_reimport(
    browser, live_server, world, tmp_path
):
    origin = f"http://event-a.events.localhost:{urlparse(live_server.url).port}"
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    requests, errors = [], []
    page.on("request", lambda req: requests.append((req.url, req.post_data or "")))
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        login(page, origin, world.o)
        page.goto(origin + "/organizer/import")
        page.wait_for_function("typeof XLSX !== 'undefined'")
        data = page.evaluate("""() => {
          const wb=XLSX.utils.book_new();
          const ws=XLSX.utils.aoa_to_sheet([['Imię','PESEL','email','Grupa','Tekst'],
            ['Ala','00000000000','synthetic@example.invalid','Zieloni','=1+1'],
            ['Ala','01234567890123456789','synthetic2@example.invalid','Zieloni','@SUM(A1)']], {origin:'B2'});
          XLSX.utils.book_append_sheet(wb,ws,'Odpowiedzi');
          XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet([['Nie zmieniaj'],['00123']]),'Drugi');
          return Array.from(new Uint8Array(XLSX.write(wb,{bookType:'xlsx',type:'array'})));
        }""")
        page.locator("#workbook").set_input_files(
            {
                "name": "synthetic.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "buffer": bytes(data),
            }
        )
        expect(page.get_by_text("Plik otwarty lokalnie", exact=False)).to_be_visible()
        page.locator("#header-row").fill("2")
        page.locator("#header-row").press("Tab")
        page.locator("#name-col").select_option("1")
        page.locator("#group-col").select_option("4")
        page.locator("#first-name-only").check()
        page.get_by_role("button", name="Przygotuj podgląd").click()
        expect(page.locator("#preview-count")).to_contain_text("2 wierszy")
        page.locator("#acknowledge").check()
        page.get_by_role("button", name="Utwórz konta", exact=True).click()
        expect(page.get_by_role("button", name="Pobierz XLSX z dostępami")).to_be_visible()
        with page.expect_download() as downloaded:
            page.get_by_role("button", name="Pobierz XLSX z dostępami").click()
        path = tmp_path / "export.xlsx"
        downloaded.value.save_as(path)
        result = page.evaluate(
            """bytes => {
          const wb=XLSX.read(new Uint8Array(bytes),{type:'array'});
          return {names:wb.SheetNames, rows:XLSX.utils.sheet_to_json(wb.Sheets.Odpowiedzi,{header:1,range:0,defval:''}),
            second:wb.Sheets.Drugi.A2.v, formula:wb.Sheets.Odpowiedzi.F3.f || null};
        }""",
            list(path.read_bytes()),
        )
        assert result["names"] == ["Odpowiedzi", "Drugi"] and result["second"] == "00123"
        assert (
            result["rows"][2][2] == "00000000000" and result["rows"][3][2] == "01234567890123456789"
        )
        assert result["rows"][2][5] == "=1+1" and result["formula"] is None
        assert len(result["rows"][2][-1]) >= 32
        uploads = [json.loads(body) for url, body in requests if url.endswith("/organizer/imports")]
        assert len(uploads) == 1
        for row in uploads[0]["rows"]:
            assert set(row) == {"row_id", "first_name", "group_ids", "login", "initial_password"}
            assert row["first_name"] == "Ala" and row["group_ids"] == [str(world.ga.pk)]
        wire = str(requests)
        assert (
            "00000000000" not in wire
            and "example.invalid" not in wire
            and "01234567890123456789" not in wire
        )
        assert all(urlparse(url).hostname == "event-a.events.localhost" for url, _ in requests)
        assert page.evaluate("localStorage.length") == 0
        responsive(page, "import")
        assert errors == []
    finally:
        context.close()
