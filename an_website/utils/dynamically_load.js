// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const bodyDiv = document.getElementById("body");

function getJSONURLWithParams(originalUrl) {
    if (originalUrl.includes("#")) {
        originalUrl = originalUrl.split("#")[0];
    }
    let [url, query] = (
        originalUrl.includes("?")
            ? originalUrl.split("?")
            : [originalUrl, ""]
    );
    let params = new URLSearchParams(query);
    params.set("as_json", "sure");
    return [url + (url.endsWith("/") ? "" : "/"), params.toString()];
}

const lastLoaded = [];
function dynLoadOnData(data, onpopstate) {
    if (!data){
        console.error("No data received");
        return;
    }
    if (data["redirect"]) {
        window.location.href = data["redirect"];
        return;
    }
    const url = data["url"];
    if (!url) {
        console.error("No URL in data ", data);
        return;
    }
    console.log("Handling data", data);
    if (!onpopstate) {
        if (lastLoaded.length === 1 && lastLoaded[0] === url) {
            console.log("Data url is the same as last loaded, ignoring");
            return;
        }
        history.pushState(
            {"data": data, "url": url, "stateType": "dynLoad"},
            data["title"],
            url
        );
    }
    if (!data["body"]) {
        window.location.reload();
        return
    }
    bodyDiv.innerHTML = data["body"];
    if (data["css"]) {
        const style = document.createElement("style");
        style.innerHTML = data["css"];
        bodyDiv.appendChild(style)
    }
    if (data["stylesheets"]) {
        for (const scriptURL of data["stylesheets"]) {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.type = "text/css"
            link.href = scriptURL;
            bodyDiv.appendChild(link);
        }
    }
    if (data["scripts"]) {
        for (const script of data["scripts"]) {
            const scriptElement = document.createElement("script");
            if (script["src"]) scriptElement.src = script["src"];
            if (script["script"]) scriptElement.innerHTML = script["script"];
            if (script["onload"]) scriptElement.onload = () => eval(script["onload"]);
            bodyDiv.appendChild(scriptElement);
        }
    }
    const title = data["title"];
    document.title = title;
    const shortTitle = data["short_title"] || title;
    let titleStyleText = `#title:after{content:"${shortTitle}"}`;
    if (shortTitle !== title) {
        titleStyleText += (
            `@media(min-width:500px){#title:after{content:"${title}"}}`
        );
    }
    document.getElementById("title-style").innerText = titleStyleText;
    dynLoadReplaceAnchors();
    window.urlData = data;
    return true
}

function dynLoadReplaceAnchors() {
    for (const anchor of document.getElementsByTagName("A")) {
        dynLoadReplaceHrefOnAnchor(anchor);
    }
}

function dynLoadReplaceHrefOnAnchor(anchor) {
    const href = anchor.href.startsWith("/")
            ? (window.location.origin + anchor.href)
            : anchor.href;
    if (
        // already dealt with
        href.startsWith("javascript:")
        // link is to different domain
        || !href.startsWith(window.location.origin)
        // link is to file, not html page
        || (
            href.split("/").pop().includes(".")
            // urls to redirect page are html pages
            && !href.startsWith(window.location.origin + "/redirect/")
        )
        // link is to /chat/, which redirects to another page
        || href.startsWith(window.location.origin + "/chat/")
    ) return;

    if (
        href.includes("#")  // if has hash
        &&
        (
            href.startsWith("#") // starts with hash -> to the same page
            ||
            (
                (
                    !window.location.hash // current url has no hash
                    && href.startsWith(window.location.href + "#")
                )
                || href.startsWith(  // is url to the same page
                    window.location.origin
                    + window.location.pathname
                    + window.location.search
                    + "#"
                )
            )
        )
    ) return;

    anchor.href = `javascript:dynLoad("${href.replace('"', '%22')}");`;
}

function dynLoad(url) {
    console.log("Loading url", url);
    history.replaceState( // save current scrollPos
        {
            "data": window.urlData,
            "url": window.location.href,
            "scrollPos": [
                document.documentElement.scrollLeft
                || document.body.scrollLeft,
                document.documentElement.scrollTop
                || document.body.scrollTop
            ],
            "stateType": "dynLoad"
        },
        document.title,
        window.location.href
    );
    dynLoadSwitchToURL(url);
}

function dynLoadSwitchToURL(url, allowSameUrl = false) {
    if (!allowSameUrl && url === window.location.href) {
        console.error("URL is the same as current, ignoring");
        return;
    }
    bodyDiv.prepend(
        "Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu."
    );
    const [requestUrl, params] = getJSONURLWithParams(url);
    get(
        requestUrl,
        params,
        (data) => dynLoadOnData(data, false),
        (error) => {
            console.log(error);
            if (url === window.location.href) {
                window.location.href = url;
            } else {
                window.location.reload();
            }
        }
    );
}

function dynLoadOnPopState(event) {
    if (event.state) {
        console.log("Popstate", event.state);
        if (!(event.state["data"] && dynLoadOnData(event.state, true))) {
            // when the data did not get handled properly
            dynLoadSwitchToURL(
                event.state["url"] || window.location.href, true
            );
        }
        if (event.state["scrollPos"]) {
            window.scrollTo(
                event.state["scrollPos"][0],
                event.state["scrollPos"][1]
            );
            return;
        }
    }
    console.error("Couldn't handle state. ", event.state);
    window.location.reload();
}

window.PopStateHandlers["dynLoad"] = dynLoadOnPopState;
// @license-end
