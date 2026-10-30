(function () {
  'use strict';

  // ---- inject CSS once ----
  if (!document.getElementById('toast-styles')) {
    var style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
      #toast-container {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 2147483647;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
        max-width: 92vw;
      }
      .toast-popup {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 22px;
        border-radius: 8px;
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #fff;
        box-shadow: 0 8px 24px rgba(0,0,0,.25);
        opacity: 0;
        transform: translateY(-8px);
        transition: opacity .25s ease, transform .25s ease;
        white-space: nowrap;
        text-align: center;
      }
      .toast-popup.show {
        opacity: 1;
        transform: translateY(0);
      }
      .toast-popup.success { background: #16a34a; }
      .toast-popup.error   { background: #dc2626; }
      .toast-popup.warning { background: #f59e0b; }
      .toast-popup.info    { background: #7c3aed; }
      .toast-popup .t-icon { font-size: 16px; line-height: 1; }
    `;
    document.head.appendChild(style);
  }

  // ---- public API ----
  window.showToast = function (message, type) {
    if (!message) return;
    type = type || 'info';

    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }

    var toast = document.createElement('div');
    toast.className = 'toast-popup ' + type;

    var icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error')   icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = '<span class="t-icon">' + icon + '</span><span></span>';
    toast.lastChild.textContent = message;   // safe: no HTML injection

    container.appendChild(toast);

    // force reflow so the transition triggers
    void toast.offsetWidth;
    toast.classList.add('show');

    setTimeout(function () {
      toast.classList.remove('show');
      setTimeout(function () { toast.remove(); }, 400);
    }, 1500);
  };

  // ---- drain Django messages on page load ----
  document.addEventListener('DOMContentLoaded', function () {
    var msgs = document.querySelectorAll('#django-messages > div');
    msgs.forEach(function (el, i) {
      var text = el.getAttribute('data-msg');
      var tag = (el.getAttribute('data-tag') || '').toLowerCase();
      var type = 'info';
      if (tag.indexOf('success') !== -1) type = 'success';
      if (tag.indexOf('error')   !== -1) type = 'error';
      if (tag.indexOf('warning') !== -1) type = 'warning';
      setTimeout(function () { window.showToast(text, type); }, i * 400);
    });
  });
})();
