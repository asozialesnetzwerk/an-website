// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
(() => {
    const resultsList = elById("search-results")!;
    const searchForm = elById("search-form") as HTMLFormElement;
    const searchInput = elById("search-input") as HTMLInputElement;

    interface Result {
        score: number;
        title: string;
        url: string;
        description: string;
    }

    function displayResults(results: Result[]) {
        resultsList.innerHTML = "";
        for (const result of results) {
            const resultElement = document.createElement("li");
            resultElement.setAttribute("score", String(result.score));
            resultElement.innerHTML = `<a href='${result.url}'>` +
                `${result.title}</a> ${result.description}`;
            resultsList.appendChild(resultElement);
        }
    }

    PopStateHandlers.search = (event: PopStateEvent) => {
        const state = event.state as { query: string; results: Result[] };
        searchInput.value = state.query;
        displayResults(state.results);
    };

    searchForm.onsubmit = (e: Event) => {
        e.preventDefault();
        return get("/api/suche", "q=" + searchInput.value, (data) => {
            displayResults(data as Result[]);
            setURLParam(
                "q",
                searchInput.value,
                {
                    query: searchInput.value,
                    results: data as Result[],
                },
                "search",
                true,
            );
        });
    };
})();
// @license-end
