/* Browser-only XLSX processing. Never upload source workbook or source row metadata. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const groups = JSON.parse($('available-groups').textContent);
  let workbook, rows, batch, selectedSheet, headerIndex, nameColumn, groupColumn;
  let finished = false, sourcePositions = [], loginColumn = -1, passwordColumn = -1;
  const status = message => { $('import-status').textContent = message; };
  const randomHex = bytes => Array.from(crypto.getRandomValues(new Uint8Array(bytes)), b => b.toString(16).padStart(2, '0')).join('');
  const option = (label, value) => { const node = document.createElement('option'); node.textContent = label; node.value = value; return node; };
  function columns() {
    if (!workbook || batch) return;
    selectedSheet = $('sheet').value;
    headerIndex = Number($('header-row').value) - 1;
    const sheet = workbook.Sheets[selectedSheet];
    const range = {s: {r: 0, c: 0}, e: XLSX.utils.decode_range(sheet['!ref'] || 'A1').e};
    rows = XLSX.utils.sheet_to_json(sheet, {header: 1, raw: true, defval: '', blankrows: true, range});
    if (rows.length > 5000 || Math.max(0, ...rows.map(r => r.length)) > 100) throw new Error('Arkusz może mieć maksymalnie 5000 wierszy i 100 kolumn. Przygotuj mniejszy eksport.');
    const headers = rows[headerIndex] || [];
    $('name-col').replaceChildren(option('Wybierz kolumnę', ''));
    $('group-col').replaceChildren(option('Bez grup', ''));
    headers.forEach((cell, i) => {
      const label = `${XLSX.utils.encode_col(i)} · ${String(cell).slice(0, 80)}`;
      $('name-col').append(option(label, String(i)));
      $('group-col').append(option(label, String(i)));
    });
    $('preview-panel').hidden = true;
  }
  $('workbook').addEventListener('change', async () => {
    try {
      const file = $('workbook').files[0];
      if (!file) return;
      if (!/\.xlsx$/i.test(file.name) || file.size > 10 * 1024**2) throw new Error('Wybierz plik .xlsx do 10 MiB.');
      if (!crypto.randomUUID) throw new Error('Import wymaga HTTPS (lokalnie: localhost).');
      workbook = XLSX.read(await file.arrayBuffer(), {type: 'array', cellDates: false, cellFormula: true, cellNF: true});
      if (workbook.vbaraw || !workbook.SheetNames.length) throw new Error('Nieobsługiwany skoroszyt.');
      batch = null; finished = false;
      $('sheet').replaceChildren(...workbook.SheetNames.map(name => option(name, name)));
      $('mapping').hidden = false;
      $('preview').disabled = false;
      columns();
      status('Plik otwarty lokalnie. Wybierz arkusz i kolumny.');
    } catch (error) { workbook = null; $('preview').disabled = true; status(error.message); }
  });
  ['sheet', 'header-row'].forEach(id => $(id).addEventListener('change', () => { try { columns(); } catch(error) { status(error.message); } }));
  ['name-col', 'group-col'].forEach(id => $(id).addEventListener('change', () => { $('preview-panel').hidden = true; }));
  $('preview').addEventListener('click', () => {
    try {
      if (!$('first-name-only').checked || $('name-col').value === '') throw new Error('Wybierz kolumnę i potwierdź, że zawiera samo imię.');
      nameColumn = Number($('name-col').value);
      groupColumn = $('group-col').value === '' ? -1 : Number($('group-col').value);
      if (nameColumn === groupColumn) throw new Error('Imię i grupa muszą być osobnymi kolumnami.');
      const headers = rows[headerIndex].map(v => String(v).trim().toLowerCase());
      loginColumn = headers.lastIndexOf('login'); passwordColumn = headers.lastIndexOf('hasło');
      const people = rows.map((row, index) => ({row, index})).filter(({row, index}) => index > headerIndex && row.some(v => v !== ''));
      if (!people.length || people.length > 500) throw new Error('Wybierz od 1 do 500 niepustych wierszy.');
      const blanks = people.filter(({row}) => !String(row[nameColumn] || '').trim());
      $('preview-count').textContent = `${people.length} wierszy · ${blanks.length} pustych imion. Powtarzające się imiona są dozwolone.`;
      if (blanks.length) throw new Error(`Uzupełnij ${blanks.length} pustych imion przed importem.`);
      sourcePositions = people.map(p => p.index);
      const labels = groupColumn < 0 ? [] : [...new Set(people.map(p => String(p.row[groupColumn] || '').trim()).filter(Boolean))];
      $('group-mapping').replaceChildren();
      labels.forEach((label, index) => {
        const wrap = document.createElement('div'); wrap.className = 'group-map-row';
        const text = document.createElement('label'); text.htmlFor = `group-${index}`; text.textContent = `Grupa w arkuszu: ${label}`;
        const select = document.createElement('select'); select.id = `group-${index}`; select.multiple = true; select.dataset.source = label;
        groups.forEach(group => { const opt = option(group.name, group.id); opt.selected = group.name === label; select.append(opt); });
        const help = document.createElement('p'); help.className = 'small muted'; help.textContent = 'Wybierz co najmniej jedną istniejącą grupę. Możesz zaznaczyć kilka.';
        wrap.append(text, select, help); $('group-mapping').append(wrap);
      });
      $('preview-panel').hidden = false;
      status('Podgląd gotowy. Żadne dane arkusza nie zostały wysłane.');
    } catch(error) { status(error.message); }
  });
  $('create').addEventListener('click', async () => {
    try {
      if (!$('acknowledge').checked) throw new Error('Potwierdź zasady przechowania dostępów.');
      if (!batch) {
        const mappings = new Map();
        $('group-mapping').querySelectorAll('select').forEach(select => {
          const ids = Array.from(select.selectedOptions, opt => opt.value);
          if (!ids.length) throw new Error('Przypisz każdą grupę z arkusza do grupy wydarzenia.');
          mappings.set(select.dataset.source, ids);
        });
        batch = {batch_id: crypto.randomUUID(), rows: sourcePositions.map(index => {
          const row = rows[index], existingLogin = loginColumn >= 0 ? String(row[loginColumn] || '').trim() : '';
          return {row_id: crypto.randomUUID(), first_name: String(row[nameColumn]).trim(), group_ids: mappings.get(String(row[groupColumn] || '').trim()) || [], login: existingLogin || `u_${randomHex(12)}`, initial_password: existingLogin ? null : randomHex(24)};
        })};
        // Freeze all mapping controls: retries must have exactly the same payload and credentials.
        ['workbook', 'sheet', 'header-row', 'name-col', 'group-col', 'preview'].forEach(id => $(id).disabled = true);
        $('group-mapping').querySelectorAll('select').forEach(select => select.disabled = true);
      }
      $('create').disabled = true;
      status('Tworzenie kont… Pozostaw tę kartę otwartą.');
      const response = await fetch('/organizer/imports', {method: 'POST', credentials: 'same-origin', cache: 'no-store', headers: {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value}, body: JSON.stringify(batch)});
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.error || 'Import nie został potwierdzony. Sprawdź logowanie i spróbuj ponownie w tej karcie.');
      finished = true;
      $('download').hidden = false;
      $('create').hidden = true;
      status('Konta gotowe. Pobierz plik z dostępami. Hasła istniejących kont nie zostały zmienione; ich dawna kolumna hasło zostanie wyczyszczona.');
    } catch(error) { $('create').disabled = false; $('create').textContent = 'Ponów ten sam import'; status(error.message); }
  });
  function safeWorkbook() {
    const result = XLSX.utils.book_new();
    workbook.SheetNames.forEach(name => {
      const source = workbook.Sheets[name], target = {};
      for (const [address, cell] of Object.entries(source)) {
        if (address.startsWith('!')) continue;
        let value = cell.v;
        if (cell.f && value == null) value = '=' + cell.f;
        if (value == null) continue;
        target[address] = {v: value, t: typeof value === 'number' ? 'n' : typeof value === 'boolean' ? 'b' : 's'};
        if (cell.z) target[address].z = cell.z;
      }
      target['!ref'] = source['!ref'] || 'A1';
      XLSX.utils.book_append_sheet(result, target, name);
    });
    return result;
  }
  $('download').addEventListener('click', () => {
    if (!finished) return;
    const result = safeWorkbook(), sheet = result.Sheets[selectedSheet];
    const range = XLSX.utils.decode_range(sheet['!ref']);
    const loginIndex = loginColumn >= 0 ? loginColumn : range.e.c + 1;
    const passwordIndex = passwordColumn >= 0 ? passwordColumn : Math.max(range.e.c, loginIndex) + 1;
    const setText = (r, c, value) => { sheet[XLSX.utils.encode_cell({r,c})] = {t:'s',v:value}; };
    setText(headerIndex, loginIndex, 'login'); setText(headerIndex, passwordIndex, 'hasło');
    batch.rows.forEach((person, i) => { setText(sourcePositions[i], loginIndex, person.login); setText(sourcePositions[i], passwordIndex, person.initial_password || ''); });
    range.e.c = Math.max(range.e.c, loginIndex, passwordIndex); sheet['!ref'] = XLSX.utils.encode_range(range);
    XLSX.writeFile(result, 'uczestnicy-z-dostepami.xlsx', {bookType:'xlsx', compression:true});
    status('Plik został przygotowany do pobrania. Sprawdź folder pobranych plików i przechowuj go bezpiecznie — zawiera oryginalne dane oraz jawne dostępy.');
  });
  window.addEventListener('beforeunload', event => { if (batch) { event.preventDefault(); event.returnValue = ''; } });
})();
