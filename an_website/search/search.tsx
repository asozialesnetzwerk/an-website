// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import {
    e as getElementById,
    get,
    PopStateHandlers,
    setURLParam,
} from "@utils/utils.js";

const resultsList = getElementById("search-results")!;
const searchForm = getElementById("search-form") as HTMLFormElement;
const searchInput = getElementById("search-input") as HTMLInputElement;

interface Result {
    score: number;
    title: string;
    url: string;
    description: string;
}

function displayResults(results: Result[]) {
    resultsList.replaceChildren(
        ...results.map((result) => (
            <li data-score={result.score}>
                <a href={result.url}>
                    {[result.title]}
                </a>
                {": "}
                {result.description}
            </li>
        )),
    );
}

PopStateHandlers["search"] = (event: PopStateEvent) => {
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
