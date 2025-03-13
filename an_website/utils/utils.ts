export const d = document;
function getElementById(id: string): HTMLElement | null {
    return d.getElementById(id);
}
export const e = getElementById;

let lastLocation = String(location);

// export function getLastLocation(): string { return lastLocation; }

export function setLastLocation(url: string): void {
    lastLocation = url;
}

const jsonContentType = "application/json";

export function post(
    url: string,
    params = {},
    ondata = console.log,
    onerror: (data: unknown) => void = console.error,
    accept = jsonContentType,
): Promise<void> {
    return fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
            "Accept": accept,
            "Content-Type": jsonContentType,
        },
    })
        .then((response) => response.json())
        .catch(onerror)
        .then(ondata)
        .catch(onerror);
}

export function get(
    url: string,
    params: Record<string, string> | string = {},
    ondata = console.log,
    onerror: (data: unknown) => void = console.error,
    accept = jsonContentType,
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
> = {};

const urlParamChangeStateType = "URLParamChange";

PopStateHandlers[urlParamChangeStateType] = () => {
    // always reload the location if URLParamChange
    location.reload();
};

export function setURLParam(
    param: string,
    value: string,
    state: unknown,
    stateType = urlParamChangeStateType,
    push = true,
) {
    return setMultipleURLParams([[param, value]], state, stateType, push);
}

export function setMultipleURLParams(
    params: [string, string][],
    state: unknown,
    stateType = urlParamChangeStateType,
    push = true,
) {
    // log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(location.search);
    params.forEach(([key, value]) => {
        urlParams.set(key, value);
    });
    const newUrl =
        `${location.origin}${location.pathname}?${urlParams.toString()}`;
    // log("newUrl", newUrl);
    (state as { stateType: string }).stateType = stateType;
    if (push && newUrl !== location.href) {
        history.pushState(state, newUrl, newUrl);
    } else {
        history.replaceState(state, newUrl, newUrl);
    }
    lastLocation = location.href;
    return newUrl;
}

function scrollToId() {
    const header = getElementById("header");
    const el = getElementById(location.hash.slice(1));
    if (header && el) {
        scrollBy(
            0,
            el.getBoundingClientRect().top - Math.floor(
                Number(getComputedStyle(header).height),
            ),
        );
    }
}
// scroll after few ms so the scroll is right on page load
setTimeout(scrollToId, 4);
window.onhashchange = scrollToId;

window.onpopstate = (event: PopStateEvent) => {
    if (lastLocation.split("#")[0] === location.href.split("#")[0]) {
        // Only hash changed
        lastLocation = location.href;
        scrollToId();
        return;
    }
    if (event.state) {
        const state = event.state as { stateType: string };
        const stateHandler = PopStateHandlers[state.stateType];
        if (stateHandler) {
            event.preventDefault();
            stateHandler(event);
            lastLocation = location.href;
            scrollToId();
            return;
        } else {
            console.error("No state handler", state);
        }
    }

    console.error("Couldn't handle", event);
    lastLocation = location.href;
    location.reload();
};

export { hideSitePane /*, showSitePane */ } from "./better_ui_.js";
export { Fragment, jsx, jsxs } from "./jsx_runtime_.js";
