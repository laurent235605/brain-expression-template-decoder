(function () {
    const STYLE_ID = 'secret-toggle-style';
    const TARGET_SELECTOR = 'input.secret-toggle-target';

    function ensureStyles() {
        if (document.getElementById(STYLE_ID)) {
            return;
        }

        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = [
            '.secret-toggle-wrap { position: relative; display: flex; align-items: center; width: 100%; }',
            '.secret-toggle-wrap > input { width: 100%; padding-right: 42px; }',
            '.secret-toggle-btn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 28px; height: 28px; border: none; border-radius: 999px; background: transparent; color: #6c757d; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; }',
            '.secret-toggle-btn:hover { background: rgba(108, 117, 125, 0.12); color: #343a40; }',
            '.secret-toggle-btn:focus-visible { outline: 2px solid #4c8bf5; outline-offset: 2px; }',
            '.secret-toggle-btn svg { width: 16px; height: 16px; pointer-events: none; }'
        ].join('');
        document.head.appendChild(style);
    }

    function getIconMarkup(isVisible) {
        if (isVisible) {
            return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3l18 18"></path><path d="M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-.58"></path><path d="M9.88 5.09A10.94 10.94 0 0112 5c5 0 9.27 3.11 11 7a11.8 11.8 0 01-4.24 5.18"></path><path d="M6.61 6.61A11.84 11.84 0 001 12c.9 2.18 2.56 4.02 4.73 5.19"></path></svg>';
        }
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    }

    function updateButton(button, input) {
        const isVisible = input.type === 'text';
        button.innerHTML = getIconMarkup(isVisible);
        button.setAttribute('aria-label', isVisible ? '隐藏密钥' : '显示密钥');
        button.title = isVisible ? '隐藏密钥' : '显示密钥';
    }

    function attachToggle(input) {
        if (!input || input.dataset.secretToggleReady === 'true') {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'secret-toggle-wrap';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'secret-toggle-btn';
        button.setAttribute('data-secret-toggle-button', 'true');
        button.addEventListener('click', function () {
            input.type = input.type === 'password' ? 'text' : 'password';
            updateButton(button, input);
        });

        wrapper.appendChild(button);
        updateButton(button, input);
        input.dataset.secretToggleReady = 'true';
    }

    function initSecretToggles() {
        ensureStyles();
        document.querySelectorAll(TARGET_SELECTOR).forEach(attachToggle);
    }

    window.initSecretToggles = initSecretToggles;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSecretToggles);
    } else {
        initSecretToggles();
    }
})();