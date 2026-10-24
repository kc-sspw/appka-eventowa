'use strict';
document.querySelectorAll('form[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!window.confirm(form.dataset.confirm)) event.preventDefault();
}));
document.querySelectorAll('.busy-form').forEach(form => form.addEventListener('submit', () => {
  form.querySelectorAll('button').forEach(button => { button.disabled = true; button.textContent = form.classList.contains('upload-form') ? 'Przesyłanie…' : 'Losowanie…'; });
  const status = form.querySelector('.busy-message');
  if (status) status.textContent = 'Czekamy na potwierdzenie magazynu. Nie zamykaj tej karty.';
}));
window.addEventListener('pageshow', event => { if (event.persisted) window.location.reload(); });
