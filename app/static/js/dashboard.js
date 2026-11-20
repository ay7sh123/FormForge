/* Dashboard: delete a form, open/close a form */
(() => {
  const list = document.getElementById('form-list');
  if (!list) return;

  list.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const row = btn.closest('.form-row');
    const id = btn.dataset.id;
    btn.closest('details')?.removeAttribute('open');

    if (btn.dataset.action === 'delete-form') {
      const ok = await FF.confirmDialog({
        title: 'Delete this form?',
        message: `“${btn.dataset.title}” and all of its responses will be permanently deleted. This can't be undone.`,
        confirmText: 'Delete form',
      });
      if (!ok) return;
      try {
        await FF.api('DELETE', `/api/forms/${id}`);
        FF.toast('Form deleted');
        row.remove();
        if (!list.querySelector('.form-row')) setTimeout(() => location.reload(), 600);
      } catch (err) {
        FF.toast(err.message, 'error');
      }
    }

    if (btn.dataset.action === 'toggle-form') {
      try {
        const { is_open } = await FF.api('POST', `/api/forms/${id}/toggle`);
        const badge = row.querySelector('[data-status]');
        badge.textContent = is_open ? 'Accepting responses' : 'Closed';
        badge.className = 'badge ' + (is_open ? 'badge-open' : 'badge-closed');
        btn.textContent = is_open ? 'Stop accepting responses' : 'Accept responses again';
        FF.toast(is_open ? 'Form is accepting responses' : 'Form is closed');
      } catch (err) {
        FF.toast(err.message, 'error');
      }
    }
  });
})();
