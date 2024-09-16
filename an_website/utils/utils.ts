// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var document = window.document;
let lastLocation = String(location);

/* export */ function getLastLocation(): string {
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
    params: Record<string, string> | string = {},
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
        location.reload();
    },
};

export function setURLParam(
    param: string,
    value: string,
    state: unknown,
    stateType = "URLParamChange",
    push = true,
) {
    return setMultipleURLParams([[param, value]], state, stateType, push);
}

export function setMultipleURLParams(
    params: [string, string][],
    state: unknown,
    stateType = "URLParamChange",
    push = true,
) {
    // log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(location.search);
    for (const [param, value] of params) {
        urlParams.set(param, value);
    }
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
    if (location.hash === "") {
        return;
    }
    const header = document.getElementById("header");
    if (!header) {
        return;
    }
    const el = document.querySelector(location.hash);
    if (!el) {
        return;
    }

    scrollBy(
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
            console.error("Couldn't find state handler for state", state);
        }
    }

    console.error("Couldn't handle state. ", event.state);
    lastLocation = location.href;
    location.reload();
};

// these functions break if using the CSS-only functionality of the site-pane
export function showSitePane() {
    document.getElementById("site-pane")?.setAttribute("open", "");
}
export function hideSitePane() {
    document.getElementById("site-pane")?.removeAttribute("open");
}
(() => {
    const openPane = document.getElementById("open-pane");
    const sitePane = document.getElementById("site-pane");

    if (!openPane || !sitePane) {
        throw Error("open-pane or site-pane not found");
    }

    const belongsToSitePane = (el: HTMLElement) => (
        el === openPane || el === sitePane || sitePane.contains(el)
    );

    // mouse users
    openPane.onmouseover = showSitePane;
    sitePane.onmouseleave = hideSitePane;

    // keyboard users
    document.onfocus = (event: FocusEvent) => {
        if (belongsToSitePane(event.target as HTMLElement)) {
            showSitePane();
        } else {
            hideSitePane();
        }
    };

    // phone users
    openPane.onclick = showSitePane;
    document.onclick = (e) => {
        belongsToSitePane(e.target as HTMLElement) || hideSitePane();
    };

    // swipe gestures (for phone users)
    const startPos: { x: number | null; y: number | null } = {
        x: null,
        y: null,
    };
    document.ontouchstart = (e) => {
        // save start pos of touch
        // @ts-expect-error TS2532
        startPos.x = e.touches[0].clientX;
        // @ts-expect-error TS2532
        startPos.y = e.touches[0].clientY;
    };
    document.ontouchmove = (e) => {
        if (startPos.x === null || startPos.y === null) {
            return;
        }
        // calculate difference
        // @ts-expect-error TS2532
        const diffX = startPos.x - e.touches[0].clientX;
        // @ts-expect-error TS2532
        const diffY = startPos.y - e.touches[0].clientY;

        // early return if just clicked, not swiped
        if (diffX === 0 && diffY === 0) {
            return;
        }

        // reset start pos
        startPos.x = null;
        startPos.y = null;

        const minDiffX = Math.max(12, 0.01 * screen.width, diffY * 1.5);

        console.debug({diffX, minDiffX});

        if (Math.abs(diffX) >= minDiffX) {
            diffX > 0 ? showSitePane() : hideSitePane();
        }
    };
})();
// @license-end
