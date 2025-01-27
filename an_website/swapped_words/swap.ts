// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import { PopStateHandlers, post, e as getElementById } from "@utils/utils.js";

const textInput = getElementById("text") as HTMLInputElement;
const configInput = getElementById(
    "config-textarea",
) as HTMLTextAreaElement;
const outputText = getElementById("output")!;
const errorText = getElementById("error-msg") as HTMLDivElement;

if (errorText.innerHTML.trim()) {
    alert(errorText.innerHTML.trim());
}

interface SwappedWordsData { // this is a mix of error data and success data
    stateType: string;
    error: string | null;
    line_num: number;
    line: string;
    text: string;
    config: string;
    replaced_text: string;
}

function ondata(
    data: SwappedWordsData | undefined,
    onpopstate = false,
) {
    if (!data) {
        console.log("data is falsy!");
        return;
    }
    if (data.error) {
        onerror(data);
        return;
    }
    if (!onpopstate) {
        data.stateType = "swappedWords";
        history.pushState(
            data,
            "Vertauschte Wörter",
            location.href,
        );
    }
    textInput.value = data.text || "";
    configInput.value = data.config || "";
    outputText.innerText = data.replaced_text || "";
    errorText.innerText = "";
}

function onerror(error: unknown) {
    const e = error as { error: string | null; line_num: number; line: string };
    console.error(e);
    if (e.error) {
        alert(e.error);
        errorText.innerText = `${e.error} In line ${e.line_num}: "${e.line}"`;
    } else {
        alert(e);
        errorText.innerText = JSON.stringify(e);
    }
}

(getElementById("form") as HTMLFormElement).onsubmit = (e) => {
    e.preventDefault();
};

(getElementById("reset")!).onclick = () =>
    post(
        "/api/vertauschte-woerter",
        {
            text: textInput.value,
            minify_config: false,
            return_config: true,
        },
        ondata,
        onerror,
    );

(getElementById("submit")!).onclick = () =>
    post(
        "/api/vertauschte-woerter",
        {
            text: textInput.value || "",
            config: configInput.value || "",
            minify_config: false,
            return_config: true,
        },
        ondata,
        onerror,
    );

PopStateHandlers["swappedWords"] = (event: PopStateEvent) => {
    if (event.state) {
        ondata(event.state as SwappedWordsData, true);
    }
};
