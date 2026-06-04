'use strict';

/* ============================================================
   _interactions.js — אנימציות ו-interactivity משותפות לכל templates
   ============================================================ */

/* ---------- 1. Scroll Reveal (IntersectionObserver) ---------- */
(function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        // stagger לפי סדר הissue בdocument
        const delay = el.dataset.delay ? parseInt(el.dataset.delay) : 0;
        setTimeout(() => el.classList.add('in-view'), delay);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  // observe כל .reveal, .reveal-scale, .kpi-hero
  function attachObserver() {
    document.querySelectorAll('.reveal, .reveal-scale, .kpi-hero-grid .kpi-hero')
      .forEach((el, i) => {
        el.dataset.delay = el.dataset.delay || (i * 55);
        observer.observe(el);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachObserver);
  } else {
    // render כבר קרה (דינאמי) — observer לאחר 100ms כדי שה-JS יסיים לבנות DOM
    setTimeout(attachObserver, 100);
  }
})();

/* ---------- 2. Theme Toggle ---------- */
(function initThemeToggle() {
  const STORAGE_KEY = 'portfolio-theme';

  function getTheme() {
    return localStorage.getItem(STORAGE_KEY) || 'dark';
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  function toggleTheme() {
    const current = getTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  // הפעל theme שמור מיד בטעינה (לפני render)
  applyTheme(getTheme());

  // הוסף כפתור לtopbar אם קיים
  function injectToggleButton() {
    const topbar = document.querySelector('.topbar');
    if (!topbar || document.getElementById('theme-toggle-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'theme-toggle-btn';
    btn.className = 'theme-toggle';
    btn.title = 'החלף מצב תאורה';
    btn.textContent = getTheme() === 'dark' ? '☀️' : '🌙';
    btn.onclick = toggleTheme;

    // הכנס לצד שמאל של ה-topbar
    topbar.style.position = 'relative';
    topbar.appendChild(btn);
    btn.style.cssText = 'position:absolute;left:16px;top:50%;transform:translateY(-50%);z-index:10';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectToggleButton);
  } else {
    setTimeout(injectToggleButton, 150);
  }
})();

/* ---------- 3. SVG Gradient Defs (לRings) ---------- */
(function injectSVGDefs() {
  if (document.getElementById('sg-defs')) return;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.id = 'sg-defs';
  svg.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
  svg.innerHTML = `
    <defs>
      <linearGradient id="grad-good" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#6ee7b7"/>
        <stop offset="100%" stop-color="#10b981"/>
      </linearGradient>
      <linearGradient id="grad-bad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#fda4af"/>
        <stop offset="100%" stop-color="#f43f5e"/>
      </linearGradient>
      <linearGradient id="grad-warn" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#fde68a"/>
        <stop offset="100%" stop-color="#f59e0b"/>
      </linearGradient>
      <linearGradient id="grad-purple" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#a78bfa"/>
        <stop offset="100%" stop-color="#7c3aed"/>
      </linearGradient>
      <linearGradient id="grad-brand" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#a78bfa"/>
        <stop offset="50%" stop-color="#6366f1"/>
        <stop offset="100%" stop-color="#f59e0b"/>
      </linearGradient>
    </defs>`;
  document.body.appendChild(svg);
})();

/* ---------- 4. Ring Animation Trigger ---------- */
function animateRings(container) {
  const rings = (container || document).querySelectorAll('.ring-fill');
  rings.forEach(path => {
    const target = path.dataset.pct || '0';
    const circumference = 2 * Math.PI * 54; // r=54
    const fill = (parseFloat(target) / 100) * circumference;
    setTimeout(() => {
      path.style.strokeDasharray = `${fill} ${circumference}`;
    }, 200);
  });
}

/* ---------- 5. Tile hover shimmer effect (CSS ::after glow) ---------- */
(function initTileShimmer() {
  document.addEventListener('mousemove', (e) => {
    const tile = e.target.closest('.tile');
    if (!tile) return;
    const rect = tile.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width * 100).toFixed(1);
    const y = ((e.clientY - rect.top) / rect.height * 100).toFixed(1);
    tile.style.setProperty('--mx', x + '%');
    tile.style.setProperty('--my', y + '%');
  });
})();
