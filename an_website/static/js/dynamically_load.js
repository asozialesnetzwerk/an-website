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
    console.log("Handling data", data);
    const url = data["url"];
    if (!onpopstate) {
        if (lastLoaded.length === 1 && lastLoaded[0] === url) {
            console.log("Data url is the same as last loaded, ignoring");
            return;
        } else {
            lastLoaded[0] = url;
        }
        history.pushState(url, url, url);
    }
    bodyDiv.innerHTML = (
        data["styles"].join("") + data["scripts"].join("") + data["body"]
    );
    document.title = data["title"];
    onLoad();
}

function onLoad() {
    const currentUrlStart = window.location.protocol + "//" + window.location.host;
    for (const anchor of document.getElementsByTagName("A")) {
        if (anchor.href.startsWith(currentUrlStart)
            && !anchor.href.endsWith("#body")
            && !anchor.href.startsWith("#")
        ) {
            const href = anchor.href;
            const [requestUrl, params] = getJSONURLWithParams(href);
            anchor.href = "#";
            anchor.onclick = () => {
                console.log("Processing anchor", href);
                if (href === window.location.href) {
                    // window.location.reload();
                } else {
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
    // window.location.reload();
}
// @license-end
