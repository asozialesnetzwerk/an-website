// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(() => {
    const textInput = elById("text");
    const configInput = elById("config-textarea");
    const outputText = elById("output");
    const errorText = elById("error_msg");

    function onerror(e) {
        error(e);
        if (e.error) {
            alert(e.error);
            errorText.innerText = `${e.error} In line ${e.line_num}: "${e.line}"`;
        } else {
            alert(e);
            errorText.innerText = e;
        }
    }

    function ondata(data, onpopstate = false) {
        if (!data) {
            log("data is falsy!")
            return;
        }
        if (data.error) return onerror(data);
        if (!onpopstate) {
            data["stateType"] = "swappedWords";
            w.history.pushState(
                data,
                "Vertauschte Wörter",
                w.location.href
            );
        }
        textInput.value = data["text"] || "";
        configInput.value = data["config"] || "";
        outputText.innerText = data["replaced_text"] || "";
        errorText.innerText = "";
    }

    elById("form").action = "javascript:void(0)";
    elById("reset").onclick = () => post(
        "/api/vertauschte-woerter",
        {
            text: textInput.value,
            minify_config: false,
            return_config: true
        },
        ondata,
        onerror
    );
    elById("submit").onclick = () => post(
        "/api/vertauschte-woerter",
        {
            text: textInput.value || "",
            config: configInput.value || "",
            minify_config: false,
            return_config: true
        },
        ondata,
        onerror
    );

    w.PopStateHandlers["swappedWords"] = (
        event
    ) => event.state && ondata(event.state, true);

})();
// @license-end
