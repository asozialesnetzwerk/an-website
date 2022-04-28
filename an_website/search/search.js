// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(() => {
    const resultsList = elById("search-results");
    const searchForm = elById("search-form");
    const searchInput = elById("search-input");

    function displayResults(results) {
        resultsList.innerHTML = "";
        for (const result of results) {
            const resultElement = d.createElement("li");
            resultElement.setAttribute(
                "score", String(result["score"])
            );
            resultElement.innerHTML = (
                `<a rel="noreferrer" href='${fixHref(result.url)}'>`
                + `${result.title}</a> ${result.description}`
            );
            resultsList.appendChild(resultElement);
        }
    }

    w.PopStateHandlers["search"] = (event) => {
        searchInput.value = event.state["query"];
        displayResults(event.state["results"]);
    }

    searchForm.action = "javascript:void(0)";
    searchForm.onsubmit = () => get(
        "/api/suche",
        "q=" + searchInput.value,
        (data) => {
            displayResults(data);
            setURLParam(
                "q",
                searchInput.value,
                {
                    "query": searchInput.value,
                    "results": data
                },
                "search",
                true
            );
        }
    );
})();
// @license-end
