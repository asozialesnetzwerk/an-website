// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
let lastLocation = String(window.location);

export function getLastLocation(): string {
    return lastLocation;
}

export function setLastLocation(url: string): void {
    lastLocation = url;
}

export function post(
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
            "Accept": accept,
            "Content-Type": "application/json",
        },
    })
        .then((response) => response.json())
        .catch(onerror)
        .then(ondata)
        .catch(onerror);
}

export function get(
    url: string,
    params: Record<string, string> = {},
    ondata = console.log,
    onerror = console.error,
    accept = "application/json",
): Promise<void> {
    const paramsString = (new URLSearchParams(params)).toString();
    return fetch(paramsString ? `${url}?${paramsString}` : url, {
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

export const PopStateHandlers: Record<
    string,
    (state: PopStateEvent) => unknown
> = {
    // always reload the location if URLParamChange
    URLParamChange: () => {
        window.location.reload();
    },
};

export function setURLParam(
    param: string,
    value: string,
    state: unknown,
    stateType = "URLParamChange",
    push = true,
) {
    // log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set(param, value);
    const newUrl =
        `${window.location.origin}${window.location.pathname}?${urlParams.toString()}`;
    // log("newUrl", newUrl);
    (state as { stateType: string }).stateType = stateType;
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
    const header = document.getElementById("header");
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
        const stateHandler = PopStateHandlers[state.stateType];
        if (stateHandler) {
            event.preventDefault();
            stateHandler(event);
            lastLocation = window.location.href;
            scrollToId();
            return;
        } else {
            console.error("Couldn't find state handler for state", state);
        }
    }

    console.error("Couldn't handle state. ", event.state);
    lastLocation = window.location.href;
    window.location.reload();
};
// @license-end
