// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
function post(
    url,
    params = {},
    ondata = (data) => console.log(data),
    onerror = (data) => console.error(data)
) {
    fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {"Accept": "application/json"}
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

function get(
    url,
    params = {},
    ondata = (data) => console.log(data),
    onerror = (data) => console.error(data)
) {
    console.log("GET", url, params);
    fetch(url + (!params ? "" : "?" + (new URLSearchParams(params)).toString()), {
        method: "GET",
        headers: {"Accept": "application/json"}
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}
// @license-end
