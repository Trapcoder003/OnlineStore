/* ============================================================
   Profile dropdown controller (shared across all templates)
   ============================================================ */
(function () {
  'use strict';

  const menu = document.getElementById('profile-menu');
  if (!menu) return;

  const trigger = menu.querySelector('.profile-trigger');
  if (!trigger) return;

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.toggle('open');
    trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target)) {
      menu.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('open')) {
      menu.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.focus();
    }
  });
})();