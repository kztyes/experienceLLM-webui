// Gradio ui update hook from stable-diffusion-webui

let uiUpdateCallbacks = []
let uiTabChangeCallbacks = []
let uiCurrentTab = null;


function gradioApp() {
    const gradioShadowRoot = document.getElementsByTagName('gradio-app')[0].shadowRoot
    return !!gradioShadowRoot ? gradioShadowRoot : document;
}

function get_uiCurrentTab() {
    return gradioApp().querySelector('.tabs button:not(.border-transparent)')
}

function get_uiCurrentTabContent() {
    return gradioApp().querySelector('.gradio-container')
}

function onUiUpdate(callback) {
    uiUpdateCallbacks.push(callback)
}

function onUiTabChange(callback) {
    uiTabChangeCallbacks.push(callback)
}

function runCallback(x, m) {
    try {
        x(m)
    } catch (e) {
        (console.error || console.log).call(console, e.message, e);
    }
}

function executeCallbacks(queue, m) {
    queue.forEach(function (x) {
        runCallback(x, m)
    })
}

document.addEventListener("DOMContentLoaded", function () {
    let mutationObserver = new MutationObserver(function (m) {
        executeCallbacks(uiUpdateCallbacks, m);
        const newTab = get_uiCurrentTab();
        if (newTab && (newTab !== uiCurrentTab)) {
            uiCurrentTab = newTab;
            executeCallbacks(uiTabChangeCallbacks);
        }
    });
    mutationObserver.observe(gradioApp(), {childList: true, subtree: true})
});

document.addEventListener('keydown', function (e) {
    let handled = false;
    if (e.key !== undefined) {
        if ((e.key === "Enter" )) handled = true;
    } else if (e.keyCode !== undefined) {
        if ((e.keyCode === 13)) handled = true;
    }
    if (handled) {
        let button = get_uiCurrentTabContent().querySelector('button[id$=_generate]');
        if (button) {
            button.click();
        }
        e.preventDefault();
    }
})
