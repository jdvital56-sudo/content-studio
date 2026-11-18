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
    const [k, nums] = norm(core); const v = dict[k]; if (!v) return null;
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
  function widget() {
    const top = document.querySelector('.top'); if (!top || document.getElementById('langseg')) return;
    const seg = document.createElement('div'); seg.className = 'tabs'; seg.id = 'langseg'; seg.style.marginLeft = '4px';
    seg.innerHTML = LANGS.map(([c, n]) => `<button class="tab ${c === lang ? 'on' : ''}" data-lang="${c}" title="Language">${n}</button>`).join('');
    const s = document.querySelector('.search'); s ? top.insertBefore(seg, s) : top.appendChild(seg);
    seg.addEventListener('click', async e => {
      const b = e.target.closest('[data-lang]'); if (!b) return; e.stopPropagation();
      try { localStorage.setItem('lang', b.dataset.lang); } catch {}
      location.reload();  // simplest and safest: every screen is rebuilt from Russian source text, then translated
    }, true);
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
