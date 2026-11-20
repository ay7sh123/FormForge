/* FormForge - shared helpers (API calls, toasts, confirm dialog, copy buttons) */
(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';

  /* ---------- fetch wrapper with CSRF token + friendly errors ---------- */
  async function api(method, url, body) {
    let res;
    try {
      res = await fetch(url, {
        method,
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-Token': csrf,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new Error('Could not reach the server. Check your connection.');
    }
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON response */ }
    if (res.status === 401) { window.location.href = '/login'; }
    if (!res.ok) throw new Error((data && data.error) || 'Something went wrong. Please try again.');
    return data;
  }

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(message, kind) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.className = 'toast show' + (kind === 'error' ? ' error' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 3200);
  }

  /* ---------- confirm dialog (returns a Promise<boolean>) ---------- */
  function confirmDialog({ title, message, confirmText = 'Delete' }) {
    const dlg = document.getElementById('confirm-dialog');
    if (!dlg || typeof dlg.showModal !== 'function') {
      return Promise.resolve(window.confirm(message));
    }
    dlg.querySelector('#confirm-title').textContent = title;
    dlg.querySelector('#confirm-message').textContent = message;
    dlg.querySelector('#confirm-ok').textContent = confirmText;
    return new Promise((resolve) => {
      dlg.addEventListener('close', () => resolve(dlg.returnValue === 'ok'), { once: true });
      dlg.returnValue = 'cancel';
      dlg.showModal();
    });
  }

  /* ---------- copy to clipboard (works on http too) ---------- */
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch { /* ignore */ }
      ta.remove();
      return ok;
    }
  }

  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-copy], [data-copy-from]');
    if (!btn) return;
    const text = btn.dataset.copy || document.querySelector(btn.dataset.copyFrom)?.value || '';
    const ok = await copyText(text);
    toast(ok ? 'Link copied' : 'Could not copy. Select the link and copy it manually.', ok ? '' : 'error');
  });

  /* ---------- close any open "More" menu when clicking elsewhere ---------- */
  document.addEventListener('click', (e) => {
    document.querySelectorAll('details.menu[open]').forEach((d) => {
      if (!d.contains(e.target)) d.removeAttribute('open');
    });
  });

  /* ---------- show times in the visitor's local time zone ---------- */
  document.querySelectorAll('time[data-local]').forEach((t) => {
    const d = new Date(t.getAttribute('datetime'));
    if (!isNaN(d)) t.textContent = d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
  });

  /* ---------- auto-hide flash messages ---------- */
  const flashes = document.querySelector('.flash-stack');
  if (flashes) setTimeout(() => { flashes.style.opacity = '0'; setTimeout(() => flashes.remove(), 400); }, 4500);

  window.FF = { api, toast, confirmDialog, copyText };
})();
