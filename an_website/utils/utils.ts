// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
const elById = (id: string) => document.getElementById(id);

let lastLocation = String(window.location);

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function getLastLocation(): string {
    return lastLocation;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setLastLocation(url: string): void {
    lastLocation = url;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function post(
    url: string,
    params = {},
    ondata = console.log,
    onerror = console.error,
    accept = "application/json",
): Promise<void> {
    return fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
            // deno-fmt-ignore
            "Accept": accept,
            "Content-Type": "application/json",
        },
    })
        .then((response) => response.json())
        .catch(onerror)
        .then(ondata)
        .catch(onerror);
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function get(
    url: string,
    params = {},
    ondata = console.log,
    onerror = console.error,
    accept = "application/json",
): Promise<void> {
    if (params) {
        url += "?" + (new URLSearchParams(params)).toString();
    }
    return fetch(url, {
        method: "GET",
        headers: { Accept: accept },
    })
        .then(
            (response) => response.json(),
        )
        .catch(onerror)
        .then(ondata)
        .catch(onerror);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PopStateHandlers: any = {
    replaceURL: (state: { origin: string }) => {
        // reload if the last location was not the one that got replaced
        lastLocation === state["origin"] || window.location.reload();
    },
    // always reload the location if URLParamChange
    URLParamChange: () => window.location.reload(),
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setURLParam(
    param: string,
    value: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    stateType = "URLParamChange",
    push = true,
) {
    // log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set(param, value);
    const newUrl =
        `${window.location.origin}${window.location.pathname}?${urlParams.toString()}`;
    // log("newUrl", newUrl);
    (state as { stateType: string })["stateType"] = stateType;
    if (push && newUrl !== window.location.href) {
        history.pushState(state, newUrl, newUrl);
    } else {
        history.replaceState(state, newUrl, newUrl);
    }
    lastLocation = window.location.href;
    return newUrl;
}

function scrollToId() {
    if (window.location.hash === "") {
        return;
    }
    const header = elById("header");
    if (!header) {
        return;
    }
    const el = document.querySelector(window.location.hash);
    if (!el) {
        return;
    }

    window.scrollBy(
        0,
        el.getBoundingClientRect().top - Math.floor(
            parseFloat(getComputedStyle(header).height),
        ),
    );
}
// scroll after few ms so the scroll is right on page load
setTimeout(scrollToId, 4);
window.onhashchange = scrollToId;

window.onpopstate = (event: PopStateEvent) => {
    if (lastLocation.split("#")[0] === window.location.href.split("#")[0]) {
        // Only hash changed
        lastLocation = window.location.href;
        scrollToId();
        return;
    }
    if (event.state) {
        const state = event.state as { stateType: string };
        if (
            state["stateType"] &&
            // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
            PopStateHandlers[state["stateType"]]
        ) {
            // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
            PopStateHandlers[state["stateType"]](event);
            lastLocation = window.location.href;
            event.preventDefault();
            scrollToId();
            return;
        }
    }

    console.error("Couldn't handle state. ", event.state);
    lastLocation = window.location.href;
    window.location.reload();
};
// @license-end
