document.addEventListener('DOMContentLoaded', () => {
  // Menu mobilne
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  // Menu rozwijane (kliknięcie; na desktopie działa też najechanie myszą)
  const dropdowns = document.querySelectorAll('[data-dropdown]');
  const closeAll = (except) => dropdowns.forEach((d) => {
    if (d !== except) {
      d.classList.remove('open');
      d.querySelector('[data-dropdown-toggle]').setAttribute('aria-expanded', 'false');
    }
  });
  dropdowns.forEach((dropdown) => {
    const button = dropdown.querySelector('[data-dropdown-toggle]');
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = dropdown.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
      closeAll(dropdown);
    });
  });
  document.addEventListener('click', () => closeAll());
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAll(); });
});

// Wyszukiwarka na żywo (książka telefoniczna)
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('[data-live-search]');
  const results = document.querySelector('[data-results]');
  if (!form || !results) return;

  const clear = form.querySelector('[data-clear]');
  const sectionField = form.querySelector('[data-section-field]');
  let timer = null;
  let controller = null;

  const run = async () => {
    const params = new URLSearchParams(new FormData(form));
    for (const [k, v] of [...params]) if (!v) params.delete(k);
    const qs = params.toString();
    const url = form.action.split('?')[0] + (qs ? `?${qs}` : '');

    if (controller) controller.abort();
    controller = new AbortController();
    try {
      const resp = await fetch(url, { headers: { 'X-Requested-With': 'fetch' }, signal: controller.signal });
      if (!resp.ok) return;
      results.innerHTML = await resp.text();
      history.replaceState(null, '', url);
      if (clear) clear.hidden = !qs;

      // Odśwież listę działów (zależy od wybranego wydziału)
      const tpl = results.querySelector('template[data-section-options]');
      if (tpl && sectionField) {
        const fresh = tpl.content.querySelector('select');
        const current = sectionField.querySelector('select');
        if (fresh && current) {
          current.innerHTML = fresh.innerHTML;
          current.value = fresh.value;
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') form.submit();
    }
  };

  form.addEventListener('input', (e) => {
    if (e.target.matches('input')) {
      clearTimeout(timer);
      timer = setTimeout(run, 250);
    }
  });
  form.addEventListener('change', (e) => {
    if (e.target.matches('select')) {
      if (e.target.name === 'department') {
        const section = form.querySelector('select[name="section"]');
        if (section) section.value = '';
      }
      run();
    }
  });
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  // Linki paginacji ładowane bez przeładowania strony
  results.addEventListener('click', (e) => {
    const link = e.target.closest('.pagination a');
    if (!link) return;
    e.preventDefault();
    const params = new URL(link.href).searchParams;
    form.querySelectorAll('[name]').forEach((el) => { el.value = params.get(el.name) || ''; });
    fetch(link.href, { headers: { 'X-Requested-With': 'fetch' } })
      .then((r) => r.text())
      .then((html) => { results.innerHTML = html; history.replaceState(null, '', link.href); window.scrollTo({ top: 0 }); });
  });
});
