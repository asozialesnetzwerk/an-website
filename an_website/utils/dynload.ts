// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import { get, PopStateHandlers, setLastLocation } from "./utils.js";
import { hideSitePane } from "./better_ui.js";

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
        window.location.href = data.redirect;
        return;
    }
    const url = data.url;
    if (!url) {
        console.error("No URL in data ", data);
        return;
    }
    console.log("Handling data", data);
    if (!onpopstate) {
        if (lastLoaded.length === 1 && lastLoaded[0] === url) {
            console.log("URL is the same as last loaded, ignoring");
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
        window.location.reload();
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

    // @ts-expect-error TS2774
    if (window.hideSitePane) {
        hideSitePane();
    }

    document.title = data.title;
    const titleElement = document.getElementById("title");
    if (titleElement) {
        titleElement.setAttribute(
            "short_title",
            data.short_title || data.title,
        );
        titleElement.innerText = data.title;
    }
    dynLoadReplaceAnchors();
    urlData = data;
    return true;
}

function dynLoadReplaceAnchors() {
    for (const anchor of document.getElementsByTagName("A")) {
        dynLoadReplaceHrefOnAnchor(anchor as HTMLAnchorElement);
    }
}

function dynLoadReplaceHrefOnAnchor(anchor: HTMLAnchorElement) {
    if (anchor.hasAttribute("no-dynload")) {
        return;
    }

    dynLoadFixHref(anchor);
}

function dynLoadFixHref(anchor: HTMLAnchorElement) {
    if (anchor.target === "_blank") {
        return;
    }

    const href = (
        anchor.href.startsWith("/")
            ? (window.location.origin + anchor.href)
            : anchor.href
    )
        .trim();

    const hrefWithoutQuery = href.split("?")[0];
    if (
        // link is to different domain
        !href.startsWith(window.location.origin) ||
        // link is to file, not HTML page
        (
            // @ts-expect-error TS2532
            (hrefWithoutQuery.split("/").pop() ?? "").includes(".") &&
            // URLs to redirect page are HTML pages
            hrefWithoutQuery !== (window.location.origin + "/redirect")
        ) ||
        // link is to /chat, which redirects to another page
        hrefWithoutQuery === (window.location.origin + "/chat")
    ) {
        return;
    }

    if (
        // URL to the same page, but with hash
        href.startsWith("#") ||
        href.startsWith(window.location.href.split("#")[0] + "#")
    ) {
        return;
    }

    // TODO: this is broken because of CSP
    anchor.onclick = (e) => {
        e.preventDefault();
        return dynLoad(href);
    };
}

function dynLoad(url: string) {
    console.log("Loading URL", url);
    history.replaceState( // save current scrollPos
        {
            data: urlData,
            url: window.location.href,
            scrollPos: [
                document.documentElement.scrollLeft || document.body.scrollLeft,
                document.documentElement.scrollTop || document.body.scrollTop,
            ],
            stateType: "dynLoad",
        },
        document.title,
        window.location.href,
    );
    return dynLoadSwitchToURL(url);
}

async function dynLoadSwitchToURL(url: string, allowSameUrl = false) {
    if (!allowSameUrl && url === window.location.href) {
        console.log("URL is the same as current, just hide site pane");
        // @ts-expect-error TS2774
        if (window.hideSitePane) {
            hideSitePane();
        }
        return;
    }
    contentContainer.prepend(
        "Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu.",
    );
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    await get(url, "", (data) => dynLoadOnData(data, false), (error) => {
        console.log(error);
        if (url === window.location.href) {
            window.location.reload();
        } else {
            window.location.href = url;
        }
    }, "application/vnd.asozial.dynload+json");
}

async function dynLoadOnPopState(event: PopStateEvent) {
    if (event.state) {
        const state = event.state as DynloadData;
        console.log("Popstate", state);
        if (
            !((event.state as { data: string }).data &&
                dynLoadOnData(state, true))
        ) {
            // when the data did not get handled properly
            await dynLoadSwitchToURL(
                state.url || window.location.href,
                true,
            );
        }
        if (state.scrollPos) {
            window.scrollTo(
                state.scrollPos[0],
                state.scrollPos[1],
            );
            return;
        }
    }
    console.error("Couldn't handle state.", event.state);
    window.location.reload();
}

PopStateHandlers.dynLoad = dynLoadOnPopState;

dynLoadReplaceAnchors();
// @license-end
