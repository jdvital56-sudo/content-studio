/* Interface languages. The app is written in Russian; other languages are dictionaries (app/i18n/<lang>.json: Russian fragment -> translation).
   Text nodes, placeholders, titles and option labels are swapped as they appear on screen, including everything rendered later.
   Add a language: python tools/i18n-translate.py tr, then add it to LANGS below. */
(function () {
  const LANGS = [['ru', 'RU'], ['uk', 'UK'], ['en', 'EN']];
  let lang = 'ru', dict = {}, busy = false;
  try { lang = localStorage.getItem('lang') || 'ru'; } catch {}
  const CYR = /[А-Яа-яЁё]/;
  const norm = s => { const nums = []; const k = s.replace(/\d+(?:[.,]\d+)?/g, m => (nums.push(m), '{n}')); return [k, nums]; };
  function tr(text) {
    if (lang === 'ru' || !CYR.test(text)) return null;
    const lead = text.match(/^\s*/)[0], trail = text.match(/\s*$/)[0], core = text.trim().replace(/\s+/g, ' ');
    const [k, nums] = norm(core); let v = dict[k];
    if (!v && nums.length) {  // "Все 19", "Черновик 3": the words are in the dictionary, the number is appended
      const base = core.replace(/\d+(?:[.,]\d+)?/g, '').replace(/\s+/g, ' ').trim();
      if (dict[base]) return lead + dict[base] + ' ' + nums.join(' ') + trail;
    }
    if (!v) return null;
    let i = 0; return lead + v.replace(/\{n\}/g, () => nums[i++] ?? '') + trail;
  }
  function walk(root) {
    if (lang === 'ru') return;
    busy = true;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: n => /^(SCRIPT|STYLE|TEXTAREA)$/.test(n.parentNode.nodeName) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
    const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
    nodes.forEach(n => { const r = tr(n.nodeValue); if (r !== null && r !== n.nodeValue) n.nodeValue = r; });
    (root.querySelectorAll ? root.querySelectorAll('[placeholder],[title],option') : []).forEach(e => {
      ['placeholder', 'title'].forEach(a => { if (e.hasAttribute(a)) { const r = tr(e.getAttribute(a)); if (r) e.setAttribute(a, r); } });
    });
    busy = false;
  }
  async function load(l) {
    if (l === 'ru') { dict = {}; return; }
    try { dict = await fetch('/i18n/' + l + '.json').then(r => r.json()); } catch { dict = {}; }
  }
  // One button with the current language; a click opens a small menu (popover) anchored to it.
  const MENU = [['ru', 'Русский', 'RU'], ['uk', 'Українська', 'UK'], ['en', 'English', 'EN'], ['tr', 'Türkçe', 'TR', 'soon'], ['es', 'Español', 'ES', 'soon']];
  function widget() {
    const top = document.querySelector('.top'); if (!top || document.getElementById('langbtn')) return;
    const wrap = document.createElement('div'); wrap.style.cssText = 'position:relative';
    const cur = MENU.find(m => m[0] === lang) || MENU[0];
    wrap.innerHTML = `<button class="btn" id="langbtn" title="Language" style="padding:6px 12px;display:flex;gap:6px;align-items:center">🌐 ${cur[2]}</button>
      <div id="langpop" style="display:none;position:absolute;right:0;top:calc(100% + 8px);min-width:200px;padding:6px;border-radius:14px;background:var(--surface);box-shadow:0 12px 40px rgba(0,0,0,.35);z-index:20;transform-origin:top right">
      ${MENU.map(([c, n, s, soon]) => `<button data-lang="${c}" ${soon ? 'disabled' : ''} style="display:flex;width:100%;align-items:center;gap:10px;border:0;background:${c === lang ? 'var(--fill)' : 'transparent'};color:var(--text);padding:9px 12px;border-radius:10px;font:inherit;text-align:left;cursor:${soon ? 'default' : 'pointer'};opacity:${soon ? .45 : 1}"><span style="width:26px;color:var(--muted);font-size:12px;font-weight:600">${s}</span><span style="flex:1">${n}</span>${c === lang ? '<span style="color:var(--accent)">✓</span>' : soon ? '<span data-i18n-skip style="font-size:11px;color:var(--muted)">soon</span>' : ''}</button>`).join('')}</div>`;
    const s = document.querySelector('.search'); s ? top.insertBefore(wrap, s) : top.appendChild(wrap);
    const pop = wrap.querySelector('#langpop');
    wrap.querySelector('#langbtn').addEventListener('click', e => { e.stopPropagation(); pop.style.display = pop.style.display === 'none' ? 'block' : 'none'; }, true);
    pop.addEventListener('click', e => {
      const b = e.target.closest('[data-lang]'); if (!b || b.disabled) return; e.stopPropagation();
      try { localStorage.setItem('lang', b.dataset.lang); } catch {}
      location.reload();  // every screen is rebuilt from the Russian source text, then translated
    }, true);
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) pop.style.display = 'none'; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') pop.style.display = 'none'; });
  }
  async function start() {
    document.documentElement.lang = lang;
    await load(lang); widget(); walk(document.body);
    new MutationObserver(ms => { if (busy || lang === 'ru') return; ms.forEach(m => { m.addedNodes.forEach(n => { if (n.nodeType === 1) walk(n); else if (n.nodeType === 3) { const r = tr(n.nodeValue); if (r !== null) n.nodeValue = r; } }); if (m.type === 'characterData') { const r = tr(m.target.nodeValue); if (r !== null && r !== m.target.nodeValue) m.target.nodeValue = r; } }); })
      .observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  window.__lang = () => lang;
  window.__tr = s => tr(s) ?? s;
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', start) : start();
})();
