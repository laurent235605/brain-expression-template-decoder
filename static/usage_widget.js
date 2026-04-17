(function () {
  'use strict';

  const WIDGET_STYLE_ID = 'usageWidgetStyles';
  const ROOT_ID = 'usageWidgetRoot';

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function slugify(text) {
    return String(text)
      .trim()
      .toLowerCase()
      .replace(/[\u4e00-\u9fa5]/g, (m) => m) // keep CJK
      .replace(/[^\w\u4e00-\u9fa5\-\s]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^\-+|\-+$/g, '');
  }

  function ensureStyles() {
    if (document.getElementById(WIDGET_STYLE_ID)) return;

    const style = document.createElement('style');
    style.id = WIDGET_STYLE_ID;
    style.textContent = `
#${ROOT_ID} { position: fixed; z-index: 9999; left: 16px; bottom: 16px; font-family: inherit; }
#${ROOT_ID} .uw-fab { 
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 18px; border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.10);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  font-weight: 800;
  font-size: 14px;
  box-shadow: 0 14px 34px rgba(0,0,0,0.26);
  cursor: pointer;
  user-select: none;
}
#${ROOT_ID} .uw-fab:hover { transform: translateY(-1px); }
#${ROOT_ID} .uw-fab:active { transform: translateY(0px); }
#${ROOT_ID} .uw-fab .uw-dot { width: 10px; height: 10px; border-radius: 999px; background: rgba(255,255,255,0.95); box-shadow: 0 0 0 3px rgba(255,255,255,0.18); }

#${ROOT_ID} .uw-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  z-index: 10000;
  opacity: 0; pointer-events: none; transition: opacity 180ms ease;
}
#${ROOT_ID}.open .uw-overlay { opacity: 1; pointer-events: auto; }

#${ROOT_ID} .uw-drawer {
  position: fixed; left: 50%; top: 50%;
  z-index: 10001;
  width: min(980px, calc(100vw - 48px));
  height: min(86vh, 920px);
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.10);
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  overflow: hidden;
  transform: translate(-50%, -50%) translateY(12px) scale(0.98);
  opacity: 0;
  pointer-events: none;
  transition: transform 220ms ease, opacity 220ms ease;
}
#${ROOT_ID}.open .uw-drawer { transform: translate(-50%, -50%) translateY(0px) scale(1); opacity: 1; pointer-events: auto; }

#${ROOT_ID} .uw-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
#${ROOT_ID} .uw-header .uw-title { font-size: 14px; font-weight: 700; letter-spacing: .2px; }
#${ROOT_ID} .uw-header .uw-actions { display: flex; gap: 8px; align-items: center; }
#${ROOT_ID} .uw-header button {
  border: 1px solid rgba(255,255,255,0.35);
  background: rgba(255,255,255,0.12);
  color: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}
#${ROOT_ID} .uw-header button:hover { background: rgba(255,255,255,0.18); }

#${ROOT_ID} .uw-body { display: grid; grid-template-columns: 240px 1fr; height: calc(100% - 48px); }
#${ROOT_ID} .uw-sidebar {
  border-right: 1px solid rgba(0,0,0,0.08);
  background: #f5f7fa;
  padding: 10px;
  overflow: auto;
}
#${ROOT_ID} .uw-content {
  padding: 12px 14px;
  overflow: auto;
  background: #fff;
}

#${ROOT_ID} .uw-search {
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.14);
  outline: none;
  margin-bottom: 10px;
}
#${ROOT_ID} .uw-search:focus { border-color: rgba(102,126,234,0.6); box-shadow: 0 0 0 3px rgba(102,126,234,0.18); }

#${ROOT_ID} .uw-toc { display: flex; flex-direction: column; gap: 6px; }
#${ROOT_ID} .uw-toc a {
  display: block;
  text-decoration: none;
  color: #2c3e50;
  padding: 6px 8px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 13px;
  line-height: 1.2;
}
#${ROOT_ID} .uw-toc a:hover { background: #ffffff; border-color: rgba(0,0,0,0.08); }
#${ROOT_ID} .uw-toc .uw-toc-section { display: block; }
#${ROOT_ID} .uw-toc .uw-toc-h1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 800;
}
#${ROOT_ID} .uw-toc .uw-toc-h1::after { content: '▸'; color: rgba(102,126,234,0.95); font-size: 12px; margin-left: 8px; }
#${ROOT_ID} .uw-toc .uw-toc-section.expanded .uw-toc-h1::after { content: '▾'; }
#${ROOT_ID} .uw-toc .uw-toc-children { display: none; margin-top: 4px; }
#${ROOT_ID} .uw-toc .uw-toc-section.expanded .uw-toc-children { display: block; }
#${ROOT_ID} .uw-toc a.level-2 { padding-left: 16px; font-size: 12.5px; opacity: 0.95; }
#${ROOT_ID} .uw-toc a.level-3 { padding-left: 24px; font-size: 12px; opacity: 0.9; }

#${ROOT_ID} .uw-md h1 { font-size: 18px; margin: 14px 0 10px; color: #2c3e50; }
#${ROOT_ID} .uw-md h2 { font-size: 16px; margin: 14px 0 10px; color: #2c3e50; }
#${ROOT_ID} .uw-md h3 { font-size: 14px; margin: 12px 0 8px; color: #2c3e50; }
#${ROOT_ID} .uw-md p { margin: 8px 0; color: #333; }
#${ROOT_ID} .uw-md ul { margin: 8px 0 8px 20px; }
#${ROOT_ID} .uw-md li { margin: 4px 0; }
#${ROOT_ID} .uw-md code { background: #f0f0f0; padding: 2px 6px; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
#${ROOT_ID} .uw-md pre { background: #1e1e1e; color: #f8f8f2; padding: 12px; border-radius: 12px; overflow: auto; margin: 10px 0; }
#${ROOT_ID} .uw-md pre code { background: transparent; padding: 0; color: inherit; }
#${ROOT_ID} .uw-muted { color: #6c757d; font-size: 13px; }
`;

    document.head.appendChild(style);
  }

  function buildMarkdownHtml(markdown) {
    // Minimal markdown rendering: headings (#..###), fenced code blocks, inline code, unordered lists, paragraphs.
    // This is intentionally lightweight (no external deps).
    const lines = String(markdown || '').replace(/\r\n/g, '\n').split('\n');

    const toc = [];
    const usedIds = new Map();

    function uniqueId(base) {
      const raw = base || 'section';
      let id = raw;
      let i = 2;
      while (usedIds.has(id)) {
        id = `${raw}-${i++}`;
      }
      usedIds.set(id, true);
      return id;
    }

    let html = '';
    let inCode = false;
    let codeLang = '';
    let codeBuf = [];
    let inUl = false;

    function closeUl() {
      if (inUl) {
        html += '</ul>';
        inUl = false;
      }
    }

    function flushParagraph(text) {
      closeUl();
      if (!text) return;
      const withInline = escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>');
      html += `<p>${withInline}</p>`;
    }

    for (const line of lines) {
      const fence = line.match(/^```\s*(.*)\s*$/);
      if (fence) {
        if (!inCode) {
          closeUl();
          inCode = true;
          codeLang = fence[1] || '';
          codeBuf = [];
        } else {
          const code = codeBuf.join('\n');
          html += `<pre><code${codeLang ? ` data-lang="${escapeHtml(codeLang)}"` : ''}>${escapeHtml(code)}</code></pre>`;
          inCode = false;
          codeLang = '';
          codeBuf = [];
        }
        continue;
      }

      if (inCode) {
        codeBuf.push(line);
        continue;
      }

      const h = line.match(/^(#{1,3})\s+(.*)$/);
      if (h) {
        closeUl();
        const level = h[1].length;
        const text = h[2].trim();
        const id = uniqueId(slugify(text) || `h${level}`);
        toc.push({ level, text, id });
        html += `<h${level} id="${escapeHtml(id)}">${escapeHtml(text)}</h${level}>`;
        continue;
      }

      const ul = line.match(/^\s*[-*]\s+(.*)$/);
      if (ul) {
        if (!inUl) {
          closeUl();
          html += '<ul>';
          inUl = true;
        }
        const item = escapeHtml(ul[1]).replace(/`([^`]+)`/g, '<code>$1</code>');
        html += `<li>${item}</li>`;
        continue;
      }

      if (!line.trim()) {
        closeUl();
        continue;
      }

      flushParagraph(line);
    }

    closeUl();

    return { html, toc };
  }

  function ensureRoot() {
    let root = document.getElementById(ROOT_ID);
    if (root) return root;

    root = document.createElement('div');
    root.id = ROOT_ID;
    root.innerHTML = `
      <div class="uw-overlay" aria-hidden="true"></div>
      <button type="button" class="uw-fab" aria-label="打开使用说明">
        <span class="uw-dot" aria-hidden="true"></span>
        <span>使用说明</span>
      </button>
      <div class="uw-drawer" role="dialog" aria-modal="true" aria-label="使用说明">
        <div class="uw-header">
          <div class="uw-title">使用说明</div>
          <div class="uw-actions">
            <button type="button" class="uw-reload" title="重新加载">刷新</button>
            <button type="button" class="uw-close" title="关闭">关闭</button>
          </div>
        </div>
        <div class="uw-body">
          <div class="uw-sidebar">
            <input class="uw-search" type="search" placeholder="搜索标题..." />
            <div class="uw-toc" aria-label="目录"></div>
          </div>
          <div class="uw-content">
            <div class="uw-muted" data-uw-status>正在加载 usage.md...</div>
            <div class="uw-md" data-uw-md style="display:none;"></div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(root);
    return root;
  }

  async function fetchUsageMarkdown() {
    const resp = await fetch('/api/usage-doc', { method: 'GET' });
    const data = await resp.json();
    if (!resp.ok || !data || !data.success) {
      const msg = (data && data.error) ? data.error : `HTTP ${resp.status}`;
      throw new Error(msg);
    }
    return data.markdown || '';
  }

  function open(root) {
    root.classList.add('open');
  }

  function close(root) {
    root.classList.remove('open');
  }

  function wire(root) {
    const overlay = root.querySelector('.uw-overlay');
    const fab = root.querySelector('.uw-fab');
    const btnClose = root.querySelector('.uw-close');
    const btnReload = root.querySelector('.uw-reload');
    const tocEl = root.querySelector('.uw-toc');
    const searchEl = root.querySelector('.uw-search');
    const statusEl = root.querySelector('[data-uw-status]');
    const mdEl = root.querySelector('[data-uw-md]');

    let cache = { markdown: null, built: null };
    const expandedSections = new Set();

    function groupToc(toc) {
      const items = (toc || []).filter(x => x.level <= 3);
      const level1Count = items.filter(x => x.level === 1).length;
      const level2Count = items.filter(x => x.level === 2).length;

      // Common doc layout: a single H1 is just the document title.
      // In that case, use H2 as the TOC top-level (expand to show H3).
      const useH2AsTop = level1Count <= 1 && level2Count > 0;

      const sections = [];
      let current = null;

      for (const h of items) {
        if (useH2AsTop) {
          if (h.level === 1) continue;
          if (h.level === 2) {
            current = { top: h, children: [] };
            sections.push(current);
            continue;
          }
          // level === 3
          if (!current) {
            current = { top: { ...h, level: 2 }, children: [] };
            sections.push(current);
            continue;
          }
          current.children.push(h);
          continue;
        }

        // Default: H1 is top-level, H2/H3 are children.
        if (h.level === 1) {
          current = { top: h, children: [] };
          sections.push(current);
          continue;
        }
        if (!current) {
          current = { top: { ...h, level: 1 }, children: [] };
          sections.push(current);
          continue;
        }
        current.children.push(h);
      }

      return { sections, useH2AsTop };
    }

    function renderToc(query) {
      const built = cache.built;
      if (!built) {
        tocEl.innerHTML = '';
        return;
      }

      const q = String(query || '').trim().toLowerCase();
      const searchMode = q.length > 0;

      const grouped = groupToc(built.toc);
      const sections = grouped.sections;
      const useH2AsTop = grouped.useH2AsTop;
      const parts = [];

      for (const section of sections) {
        const top = section.top;
        const sectionId = top.id;
        const topText = top.text || '';

        const sectionMatch = !q || topText.toLowerCase().includes(q);
        const matchedChildren = searchMode
          ? section.children.filter(c => (c.text || '').toLowerCase().includes(q))
          : section.children;

        const visible = !searchMode || sectionMatch || matchedChildren.length > 0;
        if (!visible) continue;

        const expanded = searchMode ? (matchedChildren.length > 0) : expandedSections.has(sectionId);
        const childLinks = expanded
          ? matchedChildren.map(c => {
              const cls = useH2AsTop ? 'level-3' : (c.level === 2 ? 'level-2' : 'level-3');
              return `<a class="${cls}" href="#${escapeHtml(c.id)}" data-uw-target="${escapeHtml(c.id)}">${escapeHtml(c.text)}</a>`;
            }).join('')
          : '';

        parts.push(
          `<div class="uw-toc-section ${expanded ? 'expanded' : ''}" data-uw-section="${escapeHtml(sectionId)}">` +
          `<a class="uw-toc-h1" href="#${escapeHtml(sectionId)}" data-uw-target="${escapeHtml(sectionId)}">${escapeHtml(topText)}</a>` +
          `<div class="uw-toc-children">${childLinks}</div>` +
          `</div>`
        );
      }

      tocEl.innerHTML = parts.join('');
    }

    function renderFromMarkdown(markdown) {
      const built = buildMarkdownHtml(markdown);
      mdEl.innerHTML = built.html;
      mdEl.style.display = '';
      statusEl.style.display = 'none';
      cache.built = built;

      renderToc(searchEl.value);

      // Scroll to top when re-render
      mdEl.parentElement.scrollTop = 0;
    }

    async function ensureLoaded(force) {
      if (!force && cache.markdown) return;
      statusEl.textContent = '正在加载 usage.md...';
      statusEl.style.display = '';
      mdEl.style.display = 'none';

      try {
        const markdown = await fetchUsageMarkdown();
        cache.markdown = markdown;
        renderFromMarkdown(markdown);
      } catch (e) {
        statusEl.textContent = `加载失败：${e && e.message ? e.message : String(e)}`;
        statusEl.style.display = '';
        mdEl.style.display = 'none';
      }
    }

    function applySearch() {
      renderToc(searchEl.value);
    }

    fab.addEventListener('click', async () => {
      open(root);
      await ensureLoaded(false);
    });

    overlay.addEventListener('click', () => close(root));
    btnClose.addEventListener('click', () => close(root));

    btnReload.addEventListener('click', async () => {
      cache.markdown = null;
      cache.built = null;
      await ensureLoaded(true);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close(root);
    });

    tocEl.addEventListener('click', (e) => {
      const a = e.target.closest('a[data-uw-target]');
      if (!a) return;
      e.preventDefault();

      const q = (searchEl.value || '').trim();
      const id = a.getAttribute('data-uw-target');

      // Toggle sub-headings only when clicking a top-level entry, and not in search mode.
      if (!q && a.classList.contains('uw-toc-h1')) {
        if (expandedSections.has(id)) expandedSections.delete(id);
        else expandedSections.add(id);
        renderToc(searchEl.value);
      }

      const target = mdEl.querySelector(`#${CSS.escape(id)}`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    searchEl.addEventListener('input', applySearch);

    // Preload lazily after page settles
    window.setTimeout(() => {
      ensureLoaded(false).catch(() => {});
    }, 800);
  }

  function init() {
    ensureStyles();
    const root = ensureRoot();
    wire(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
