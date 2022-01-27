// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
(() => {
    const textInput = document.getElementById("text");
    const configInput = document.getElementById("config-textarea");
    const outputText = document.getElementById("output");
    const errorText = document.getElementById("error_msg");

    function onerror(error) {
        console.error(error);
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
            console.log("data is falsy!")
            return;
        }
        if (data.error) return onerror(data);
        if (!onpopstate) {
            data["stateType"] = "swappedWords";
            window.history.pushState(
                data,
                "Vertauschte Wörter",
                window.location.href
            );
        }
        textInput.value = data["text"] || "";
        configInput.value = data["config"] || "";
        outputText.innerText = data["replaced_text"] || "";
        errorText.innerText = "";
    }

    function onSubmit() {
        post(
            "/api/vertauschte-woerter/",
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
            "/api/vertauschte-woerter/",
            {
                text: textInput.value,
                minify_config: false,
                return_config: true
            },
            ondata,
            onerror
        )
    }

    document.getElementById("form").action = "javascript:void(0)";
    document.getElementById("reset").onclick = onReset;
    document.getElementById("submit").onclick = onSubmit;

    window.PopStateHandlers["swappedWords"] = (event) => (
        event.state && ondata(event.state, true)
    );

})();
// @license-end
