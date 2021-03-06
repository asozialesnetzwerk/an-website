// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
const w = window;
const d = document;
const elById = (id) => d.getElementById(id);
const log = console.log;
const error = console.error;

w.lastLocation = String(w.location);

function post(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
            "Accept": "application/json", "Content-Type": "application/json"
        }
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

function get(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    if (params) url += "?" + (new URLSearchParams(params)).toString()
    fetch(
        url,
        {
            method: "GET",
            headers: {"Accept": "application/json"}
        }
    ).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

w.PopStateHandlers = {
    "replaceURL": (state) => {
        // reload if the last location was not the one that got replaced
        w.lastLocation === state["origin"] || w.location.reload();
    },
    // always reload the location if URLParamChange
    "URLParamChange": (s) => w.location.reload()
};

function setURLParam(
    param,
    value,
    state,
    stateType = "URLParamChange",
    push = true
) {
    //log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(w.location.search);
    urlParams.set(param, value);
    const newUrl = `${w.location.origin}${w.location.pathname}?${urlParams.toString()}`;
    //log("newUrl", newUrl);
    state["stateType"] = stateType;
    if (push && newUrl !== w.location.href) {
        history.pushState(state, newUrl, newUrl);
    } else {
        history.replaceState(state, newUrl, newUrl)
    }
    w.lastLocation = w.location.href;
    return newUrl;
}

function scrollToId() {
    if (w.location.hash === "") return;
    const el = d.querySelector(w.location.hash);
    if (!el) return;
    w.scrollBy(
        0,
        el.getBoundingClientRect().top - Math.floor(
            parseFloat(getComputedStyle(elById("header")).height)
        )
    );
}
// scroll after few ms so the scroll is right on page load
setTimeout(scrollToId, 4);
w.onhashchange = scrollToId;

w.onpopstate = (event) => {
    if (
        w.lastLocation.split("#")[0]
        === w.location.href.split("#")[0]
    ) {
        // Only hash changed
        w.lastLocation = w.location.href;
        scrollToId();
        return;
    }
    if (
        event.state
        && event.state["stateType"]
        && w.PopStateHandlers[event.state["stateType"]]
    ) {
        w.PopStateHandlers[event.state["stateType"]](event);
        w.lastLocation = w.location.href;
        event.preventDefault();
        scrollToId();
        return;
    }
    error("Couldn't handle state. ", event.state);
    w.lastLocation = w.location.href;
    w.location.reload();
}

function fixHref(href) {
    if (w.dynLoadGetFixedHref)
        return w.dynLoadGetFixedHref(href);
    // if the function doesn't exist don't change anything
    return href;
}
// @license-end
