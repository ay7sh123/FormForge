/* Form builder: add / edit / reorder questions, then save through the JSON API */
(() => {
  const dataEl = document.getElementById('form-data');
  if (!dataEl) return;

  const TYPES = [
    { value: 'short_answer', label: 'Short answer', hint: 'Short answer text' },
    { value: 'paragraph', label: 'Paragraph', hint: 'Long answer text' },
    { value: 'email', label: 'Email', hint: 'name@example.com' },
    { value: 'number', label: 'Number', hint: '123' },
    { value: 'date', label: 'Date', hint: 'Month, day, year' },
  ];
  const typeInfo = (v) => TYPES.find((t) => t.value === v) || TYPES[0];

  const ICONS = {
    up: '<path d="M4 10l4-4 4 4"/>',
    down: '<path d="M4 6l4 4 4-4"/>',
    copy: '<rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 3.5h-6a1 1 0 0 0-1 1v6"/>',
    trash: '<path d="M3 4.5h10M6.5 4.5V3h3v1.5M5 4.5l.5 8h5l.5-8"/>',
  };
  const icon = (name) =>
    `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const uid = () => {
    const bytes = new Uint8Array(6);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  };

  /* ---------- state ---------- */
  const state = JSON.parse(dataEl.textContent);
  if (!state.id && !state.questions.length) {
    state.questions.push({ id: uid(), label: '', type: 'short_answer', required: false });
  }
  let dirty = false;
  let saving = false;

  const $ = (sel) => document.querySelector(sel);
  const titleEl = $('#form-title');
  const descEl = $('#form-desc');
  const listEl = $('#questions');
  const saveBtn = $('#save-btn');
  const statusEl = $('#save-status');
  const shareEl = $('#share-panel');
  const addBar = $('#add-bar');

  function setStatus(text, stateName) {
    statusEl.textContent = text;
    statusEl.dataset.state = stateName;
  }
  function markDirty() {
    if (!dirty) { dirty = true; setStatus('Unsaved changes', 'dirty'); }
  }

  /* ---------- rendering ---------- */
  function render() {
    if (!state.questions.length) {
      listEl.innerHTML = '<div class="q-empty"><p>No questions yet. Use the buttons below to add one.</p></div>';
      return;
    }
    const last = state.questions.length - 1;
    listEl.innerHTML = state.questions.map((q, i) => `
      <article class="q" data-id="${q.id}" aria-label="Question ${i + 1}">
        <div class="q-top">
          <span class="q-index">Question ${i + 1}</span>
          <div class="q-tools">
            <button type="button" class="icon-btn" data-action="up" aria-label="Move question ${i + 1} up" ${i === 0 ? 'disabled' : ''}>${icon('up')}</button>
            <button type="button" class="icon-btn" data-action="down" aria-label="Move question ${i + 1} down" ${i === last ? 'disabled' : ''}>${icon('down')}</button>
            <button type="button" class="icon-btn" data-action="duplicate" aria-label="Duplicate question ${i + 1}">${icon('copy')}</button>
            <button type="button" class="icon-btn danger" data-action="delete" aria-label="Delete question ${i + 1}">${icon('trash')}</button>
          </div>
        </div>
        <label class="sr-only" for="label-${q.id}">Question ${i + 1} text</label>
        <input id="label-${q.id}" class="q-label" type="text" data-field="label" maxlength="300"
               placeholder="Type your question" autocomplete="off" value="${esc(q.label)}">
        <div class="q-preview ${q.type}">${esc(typeInfo(q.type).hint)}</div>
        <div class="q-foot">
          <label class="select">Answer type
            <select data-field="type">
              ${TYPES.map((t) => `<option value="${t.value}" ${t.value === q.type ? 'selected' : ''}>${t.label}</option>`).join('')}
            </select>
          </label>
          <label class="switch">
            <input type="checkbox" data-field="required" ${q.required ? 'checked' : ''}>
            <span class="track"></span>
            <span>Required</span>
          </label>
        </div>
      </article>`).join('');
  }

  function findQuestion(el) {
    const id = el.closest('.q')?.dataset.id;
    return state.questions.find((q) => q.id === id);
  }

  /* ---------- events ---------- */
  titleEl.addEventListener('input', () => { state.title = titleEl.value; titleEl.classList.remove('invalid'); markDirty(); });
  descEl.addEventListener('input', () => { state.description = descEl.value; markDirty(); });

  listEl.addEventListener('input', (e) => {
    const field = e.target.closest('[data-field="label"]');
    if (!field) return;
    findQuestion(field).label = field.value;
    field.classList.remove('invalid');
    markDirty();
  });

  listEl.addEventListener('change', (e) => {
    const field = e.target.closest('[data-field]');
    if (!field) return;
    const q = findQuestion(field);
    if (field.dataset.field === 'type') {
      q.type = field.value;
      const preview = field.closest('.q').querySelector('.q-preview');
      preview.className = `q-preview ${q.type}`;
      preview.textContent = typeInfo(q.type).hint;
    } else if (field.dataset.field === 'required') {
      q.required = field.checked;
    }
    markDirty();
  });

  listEl.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const id = btn.closest('.q').dataset.id;
    const idx = state.questions.findIndex((q) => q.id === id);
    const action = btn.dataset.action;
    let focusId = id;

    if (action === 'up' && idx > 0) {
      [state.questions[idx - 1], state.questions[idx]] = [state.questions[idx], state.questions[idx - 1]];
    } else if (action === 'down' && idx < state.questions.length - 1) {
      [state.questions[idx + 1], state.questions[idx]] = [state.questions[idx], state.questions[idx + 1]];
    } else if (action === 'duplicate') {
      const copy = { ...state.questions[idx], id: uid() };
      state.questions.splice(idx + 1, 0, copy);
      focusId = copy.id;
    } else if (action === 'delete') {
      state.questions.splice(idx, 1);
      focusId = null;
    }
    markDirty();
    render();

    if (focusId) {
      const target = listEl.querySelector(`[data-id="${focusId}"]`);
      const keep = action === 'duplicate' ? '.q-label' : `[data-action="${action}"]:not(:disabled)`;
      (target?.querySelector(keep) || target?.querySelector('.q-label'))?.focus();
    } else {
      addBar.querySelector('.chip').focus();
    }
  });

  addBar.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-add]');
    if (!btn) return;
    if (state.questions.length >= 50) { FF.toast('A form can have at most 50 questions.', 'error'); return; }
    const q = { id: uid(), label: '', type: btn.dataset.add, required: false };
    state.questions.push(q);
    markDirty();
    render();
    const input = listEl.querySelector(`[data-id="${q.id}"] .q-label`);
    input.focus();
    input.scrollIntoView({ block: 'center', behavior: 'smooth' });
  });

  /* ---------- share panel ---------- */
  function showShare() {
    if (!state.public_id) return;
    const url = `${location.origin}/f/${state.public_id}`;
    $('#share-url').value = url;
    $('#share-open').href = url;
    shareEl.hidden = false;
    if (state.id && !$('#responses-link')) {
      const a = document.createElement('a');
      a.id = 'responses-link';
      a.className = 'btn btn-secondary btn-sm';
      a.href = `/forms/${state.id}/responses`;
      a.textContent = 'Responses';
      saveBtn.before(a);
    }
  }

  /* ---------- saving ---------- */
  function validate() {
    let firstBad = null;
    if (!state.title.trim()) { titleEl.classList.add('invalid'); firstBad = titleEl; }
    state.questions.forEach((q) => {
      if (!q.label.trim()) {
        const el = listEl.querySelector(`[data-id="${q.id}"] .q-label`);
        el.classList.add('invalid');
        firstBad = firstBad || el;
      }
    });
    if (!state.questions.length) { FF.toast('Add at least one question before saving.', 'error'); return false; }
    if (firstBad) {
      firstBad.focus();
      FF.toast('Fill in the highlighted fields to save.', 'error');
      return false;
    }
    return true;
  }

  async function save() {
    if (saving || !validate()) return;
    saving = true;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    const payload = {
      title: state.title.trim(),
      description: state.description.trim(),
      questions: state.questions.map(({ id, label, type, required }) => ({ id, label: label.trim(), type, required })),
    };
    try {
      const wasNew = !state.id;
      const { form } = wasNew
        ? await FF.api('POST', '/api/forms', payload)
        : await FF.api('PUT', `/api/forms/${state.id}`, payload);
      Object.assign(state, form);
      titleEl.value = state.title;
      descEl.value = state.description;
      render();
      dirty = false;
      setStatus('All changes saved', 'saved');
      showShare();
      if (wasNew) {
        history.replaceState(null, '', `/forms/${state.id}/edit`);
        window.scrollTo({ top: 0, behavior: 'smooth' }); // reveal the new share link
      }
      FF.toast('Form saved');
    } catch (err) {
      FF.toast(err.message, 'error');
    } finally {
      saving = false;
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save form';
    }
  }

  saveBtn.addEventListener('click', save);
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); save(); }
  });
  window.addEventListener('beforeunload', (e) => {
    if (dirty) { e.preventDefault(); e.returnValue = ''; }
  });

  /* ---------- initial paint ---------- */
  titleEl.value = state.title;
  descEl.value = state.description;
  render();
  showShare();
  if (!state.id) { dirty = false; setStatus('Not saved yet', 'saved'); }
})();
