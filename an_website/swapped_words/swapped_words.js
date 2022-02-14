// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
(() => {
    const textInput = elById("text");
    const configInput = elById("config-textarea");
    const outputText = elById("output");
    const errorText = elById("error_msg");

    function onerror(error) {
        error(error);
        if (error.error) {
            alert(error.error);
            errorText.innerText = `${error.error} In line ${error.line_num}: "${error.line}"`;
        } else {
            alert(error);
            errorText.innerText = error;
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

    function onSubmit() {
        post(
            "/api/vertauschte-woerter",
            {
                text: textInput.value || "",
                config: configInput.value || "",
                minify_config: false,
                return_config: true
            },
            ondata,
            onerror
        )
    }

    function onReset() {
        post(
            "/api/vertauschte-woerter",
            {
                text: textInput.value,
                minify_config: false,
                return_config: true
            },
            ondata,
            onerror
        )
    }

    elById("form").action = "javascript:void(0)";
    elById("reset").onclick = onReset;
    elById("submit").onclick = onSubmit;

    w.PopStateHandlers["swappedWords"] = (event) => (
        event.state && ondata(event.state, true)
    );

})();
// @license-end
