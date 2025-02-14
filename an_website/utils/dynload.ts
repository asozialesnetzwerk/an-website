// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import {
    d,
    e as getElementById,
    get,
    hideSitePane,
    PopStateHandlers,
    setLastLocation,
} from "@utils/utils.js";

const contentContainer = getElementById("main") as HTMLDivElement;

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
        location.reload();
        return;
    }

    // d.onkeyup = () => {}; // not used in any JS file
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    d.onkeydown = () => {}; // remove keydown listeners

    contentContainer.innerHTML = data.body;
    if (data.css) {
        const style = d.createElement("style");
        style.innerHTML = data.css;
        contentContainer.appendChild(style);
    }
    for (const scriptURL of data.stylesheets) {
        const link = d.createElement("link");
        link.rel = "stylesheet";
        link.type = "text/css";
        link.href = scriptURL;
        contentContainer.appendChild(link);
    }
    for (const script of data.scripts) {
        if (script.src) {
            const scriptElement = d.createElement("script");
            scriptElement.type = script.type;
            scriptElement.src = script.src;
            contentContainer.appendChild(scriptElement);
        } else {
            console.error("Script without src", script);
        }
    }

    hideSitePane();

    d.title = data.title;
    const titleElement = getElementById("title");
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
    console.log("Loading URL", url);
    history.replaceState( // save current scrollPos
        {
            data: urlData,
            url: location.href,
            scrollPos: [
                d.documentElement.scrollLeft || d.body.scrollLeft,
                d.documentElement.scrollTop || d.body.scrollTop,
            ],
            stateType: "dynLoad",
        },
        d.title,
        location.href,
    );
    return dynLoadSwitchToURL(url);
}

async function dynLoadSwitchToURL(url: string, allowSameUrl = false) {
    if (!allowSameUrl && url === location.href) {
        console.log("URL is the same as current, just hide site pane");
        hideSitePane();
        return;
    }
    contentContainer.prepend(
        "Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu.",
    );
    await get(
        url,
        "",
        (data: DynloadData) => dynLoadOnData(data, false),
        (error: unknown) => {
            console.log(error);
            if (url === location.href) {
                location.reload();
            } else {
                location.href = url;
            }
        },
        "application/vnd.asozial.dynload+json",
    );
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

d.addEventListener("click", (e: DocumentEventMap["click"]) => {
    const anchor = (e.target as HTMLElement | undefined)?.closest("a") as
        | HTMLAnchorElement
        | undefined;
    console.debug({ msg: "clicked on: ", target: e.target, anchor });

    if (
        // anchor not found
        !anchor ||
        // not supposed to be opened inline
        anchor.target === "_blank" ||
        // link should not be dynloaded
        anchor.hasAttribute("no-dynload")
    ) {
        console.debug("Ignoring click.");
        return;
    }

    const anchor_url = (anchor.href.startsWith("/") ? location.origin : "") +
        anchor.href;

    if (
        // URL to the same page, but with hash
        anchor_url.startsWith("#") ||
        anchor_url.startsWith(`${location.href.split("#")[0]}#`) ||
        // link is to different domain
        !anchor_url.startsWith(location.origin)
    ) {
        console.log({ msg: "cannot handle click", anchor, anchor_url });
        return;
    }

    e.preventDefault();

    void dynLoad(anchor_url).then(() => {
        console.log("blurring", anchor);
        anchor.blur();
    });
});
