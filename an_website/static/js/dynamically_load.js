// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const bodyDiv = document.getElementById("body");

function getJSONURLWithParams(originalUrl) {
    if (originalUrl.includes("#")) {
        originalUrl = originalUrl.split("#")[0];
    }
    let [url, params] = (
        originalUrl.includes("?")
            ? originalUrl.split("?")
            : [originalUrl, ""]
    );
    return [url + (url.endsWith("/") ? "" : "/") + "json/", params];
}

const lastLoaded = [];
function onData(data, onpopstate) {
    if (!data) {
        return;
    }
    const url = data["url"];
    console.log("Handling data", url);
    if (!onpopstate) {
        if (lastLoaded.length === 1 && lastLoaded[0] === url) {
            console.log("Data url is the same as last loaded, ignoring");
            return;
        }
        history.pushState(url, url, url);
    }
    // lastLoaded[0] = url;
    bodyDiv.innerHTML = data["body"];
    if (data["css"]) {
        const style = document.createElement("style");
        style.innerHTML = data["css"];
        bodyDiv.appendChild(style)
    }
    for (const scriptURL of data["stylesheets"]) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.type = "text/css"
        link.href = scriptURL;
        bodyDiv.appendChild(link);
    }
    for (const script of data["scripts"]) {
        const scriptElement = document.createElement("script");
        if (script["src"]) scriptElement.src = script["src"];
        if (script["script"]) scriptElement.innerHTML = script["script"];
        if (script["onload"]) scriptElement.onload = () => eval(script["onload"]);
        bodyDiv.appendChild(scriptElement);
    }
    document.title = data["title"];
    replaceAnchors();
}

function replaceAnchors() {
    for (const anchor of document.getElementsByTagName("A")) {
        const href = anchor.href;
        if (href.includes("#")) {
            console.log(href)
        }
        if (
            // link is to same domain
            (href.startsWith(window.location.origin) || href.startsWith("/"))
            && // check if it is a link to this page with a hash
            !( // invert bool
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
                        || href.startsWith( // is a real url to the same page
                            window.location.pathname
                            + window.location.search
                            + "#"
                        )
                        || href.startsWith(  // is url to the same page
                            window.location.origin
                            + window.location.pathname
                            + window.location.search
                            + "#"
                        )
                    )
                )
            )
        ) {
            const [requestUrl, params] = getJSONURLWithParams(href);
            anchor.href = "javascript:void(0);";
            anchor.onclick = () => {
                console.log("Processing anchor", href);
                if (href !== window.location.href) {
                    bodyDiv.innerHTML = "Loading...";
                    get(
                        requestUrl,
                        params,
                        (data) => onData(data, false),
                        (error) => {
                            console.log(error);
                            window.location.href = href;
                        }
                    );
                }
            };
        }
    }
}

window.onpopstate = (event) => {
    if (event.state) {
        const [url, params] = getJSONURLWithParams(event.state)
        if (url && params) {
            get(
                url,
                params,
                (data) => onData(data, true),
                (error) => {
                    console.error(error);
                    window.location.reload();
                }
            );
            return;
        }
    }
    console.error("Couldn't handle state. ", event.state);
    window.location.reload();
}
// @license-end
