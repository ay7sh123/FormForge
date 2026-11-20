/* Responses page: delete a single response */
(() => {
  const area = document.getElementById('table-area');
  if (!area) return;

  area.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action="delete-response"]');
    if (!btn) return;
    const ok = await FF.confirmDialog({
      title: 'Delete this response?',
      message: 'This response will be permanently removed.',
      confirmText: 'Delete response',
    });
    if (!ok) return;
    try {
      const { count } = await FF.api('DELETE', `/api/forms/${area.dataset.formId}/responses/${btn.dataset.id}`);
      btn.closest('tr').remove();
      document.getElementById('response-count').textContent = count;
      FF.toast('Response deleted');
      if (count === 0) setTimeout(() => location.reload(), 600);
    } catch (err) {
      FF.toast(err.message, 'error');
    }
  });
})();
