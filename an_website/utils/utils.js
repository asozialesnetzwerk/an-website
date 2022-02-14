// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const w = window;
const d = document;
const elById = (id) => d.getElementById(id);
const log = console.log;
const error = console.error;

w.lastLocation = w.location;

function post(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {"Accept": "application/json"}
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

function get(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    // log("GET", url, params);
    fetch(url + (!params ? "" : "?" + (new URLSearchParams(params)).toString()), {
        method: "GET",
        headers: {"Accept": "application/json"}
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

w.PopStateHandlers = {
    "replaceURL": (state) => {
        // reload if the last location was not the one that got replaced
        w.lastLocation === state["origin"] || w.location.reload();
    },
    "URLParamChange": (state) => {
        w.location.reload();
    }
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
    if (push) {
        history.pushState(state, newUrl, newUrl);
    } else {
        history.replaceState(state, newUrl, newUrl)
    }
    return newUrl;
}

w.onpopstate = (event) => {
    if (event.state
        && event.state["stateType"]
        && w.PopStateHandlers[event.state["stateType"]]) {
        w.PopStateHandlers[event.state["stateType"]](event);
        w.lastLocation = w.location;
    } else {
        error("Couldn't handle state. ", event.state);
        w.location.reload();
    }
}

function fixHref(href) {
    if (w.dynLoadGetFixedHref) {
        return w.dynLoadGetFixedHref(href);
    }
    return href;
}
// @license-end
