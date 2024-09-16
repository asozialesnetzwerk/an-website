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

export const enableDynload = () => {
    const contentContainer = document.getElementById("main") as HTMLDivElement;

    let urlData = {};

    const lastLoaded: [] | [string] = [];

    interface DynloadData {
        body: string;
        css: string;
        redirect: string;
        scripts: { type: string; src: string | null }[];
        scrollPos?: [number, number];
        short_title: string;
        stylesheets: string[];
        title: string;
        url: string;
    }

    function dynLoadOnData(
        data: DynloadData | undefined,
        onpopstate: boolean,
    ) {
        if (!data) {
            console.error("No data received");
            return;
        }
        if (data.redirect) {
            location.href = data.redirect;
            return;
        }
        const url = data.url;
        if (!url) {
            console.error("No URL in data ", data);
            return;
        }
        console.debug("Handling data", data);
        if (!onpopstate) {
            if (lastLoaded.length === 1 && lastLoaded[0] === url) {
                console.debug("URL is the same as last loaded, ignoring");
                return;
            }
            history.pushState(
                { data, url, stateType: "dynLoad" },
                data.title,
                url,
            );
            setLastLocation(url);
        }
        if (!data.body) {
            location.reload();
            return;
        }

        // d.onkeyup = () => {}; // not used in any JS file
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        document.onkeydown = () => {}; // remove keydown listeners

        contentContainer.innerHTML = data.body;
        if (data.css) {
            const style = document.createElement("style");
            style.innerHTML = data.css;
            contentContainer.appendChild(style);
        }
        for (const scriptURL of data.stylesheets) {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.type = "text/css";
            link.href = scriptURL;
            contentContainer.appendChild(link);
        }
        for (const script of data.scripts) {
            if (script.src) {
                const scriptElement = document.createElement("script");
                scriptElement.type = script.type;
                scriptElement.src = script.src;
                contentContainer.appendChild(scriptElement);
            } else {
                console.error("Script without src", script);
            }
        }

        hideSitePane?.()

        document.title = data.title;
        const titleElement = document.getElementById("title");
        if (titleElement) {
            titleElement.setAttribute(
                "short_title",
                data.short_title || data.title,
            );
            titleElement.innerText = data.title;
        }
        urlData = data;
        return true;
    }

    function dynLoad(url: string) {
        console.debug("Loading URL", url);
        history.replaceState( // save current scrollPos
            {
                data: urlData,
                url: location.href,
                scrollPos: [
                    document.documentElement.scrollLeft || document.body.scrollLeft,
                    document.documentElement.scrollTop || document.body.scrollTop,
                ],
                stateType: "dynLoad",
            },
            document.title,
            location.href,
        );
        return dynLoadSwitchToURL(url);
    }

    async function dynLoadSwitchToURL(url: string, allowSameUrl = false) {
        if (!allowSameUrl && url === location.href) {
            console.debug("URL is the same as current, just hide site pane");
            hideSitePane?.()
            return;
        }
        contentContainer.prepend(
            "Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu.",
        );
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        await get(url, "", (data) => dynLoadOnData(data, false), (error) => {
            if (url === location.href) {
                location.reload();
            } else {
                location.href = url;
            }
        }, "application/vnd.asozial.dynload+json");
    }

    async function dynLoadOnPopState(event: PopStateEvent) {
        if (event.state) {
            const state = event.state as DynloadData;
            console.debug("Popstate", state);
            if (
                !((event.state as { data: string }).data &&
                    dynLoadOnData(state, true))
            ) {
                // when the data did not get handled properly
                await dynLoadSwitchToURL(
                    state.url || location.href,
                    true,
                );
            }
            if (state.scrollPos) {
                scrollTo(
                    state.scrollPos[0],
                    state.scrollPos[1],
                );
                return;
            }
        }
        console.error("Couldn't handle state.", event.state);
        location.reload();
    }

    PopStateHandlers["dynLoad"] = dynLoadOnPopState;

    document.addEventListener("click", (e) => {
        if ((e.target as HTMLElement | undefined)?.tagName !== "A") {
            return;
        }

        const anchor = e.target as HTMLAnchorElement;
        if (anchor.target === "_blank") {
            return;
        }

        const origin = location.origin;

        const href = (
            anchor.href.startsWith("/")
                ? (origin + anchor.href)
                : anchor.href
        )
            .trim();

        const hrefWithoutQuery = href.split("?")[0];
        if (
            // link is to different domain
            !href.startsWith(origin) ||
            // link is to file, not HTML page
            (
                // @ts-expect-error TS2532
                (hrefWithoutQuery.split("/").pop() ?? "").includes(".") &&
                // URLs to redirect page are HTML pages
                hrefWithoutQuery !== (origin + "/redirect")
            ) ||
            // link is to /chat, which redirects to another page
            hrefWithoutQuery === (origin + "/chat")
        ) {
            return;
        }

        if (
            // URL to the same page, but with hash
            href.startsWith("#") ||
            href.startsWith(location.href.split("#")[0] + "#")
        ) {
            return;
        }
        e.preventDefault();
        return dynLoad(href);
    });
};
// @license-end
