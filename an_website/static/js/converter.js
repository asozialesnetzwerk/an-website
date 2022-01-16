// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
(() => {
    const output = document.getElementById("output");
    const submitButton = document.getElementById("submit");

    const fields = [
        document.getElementById("euro"),
        document.getElementById("mark"),
        document.getElementById("ost"),
        document.getElementById("schwarz")
    ];
    const factors = [
        1n, //Euro
        2n, //Deutsche Mark
        4n, //Ostmark
        20n //Ostmark auf dem Schwarzmarkt
    ];

    const numberRegex = /^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/;

    function getDisplayValue(wert) {
        if (typeof wert === "string") {
            wert = strToBigInt(wert);
        }
        if (typeof wert !== "bigint") {
            alert(`Ungültiger Wert ${wert} mit type ${typeof wert}`);
        }
        let str = wert.toString();
        if (str.length === 1) {
            if (str === "0") {
                return "0";
            }
            str = "0" + str;
        }
        if (str.length === 2) {
            if (str === "00") {
                return "0";
            }
            return "0," + str
        } else if (str.endsWith("00")) {
            return str.slice(0, str.length - 2);
        } else {
            return str.slice(0, str.length - 2) + "," + str.slice(str.length - 2);
        }
    }

    function strToBigInt(str) {
        if (!str) {
            return 0n;
        }
        let preComma, postComma;
        if (str.includes(",")) {
            [preComma, postComma] = str.split(",");
        } else if (str.includes(".")) {
            [preComma, postComma] = str.split(".");
        } else {
            preComma = str;
            postComma = "00";
        }
        if (postComma.length !== 2) {
            postComma = (postComma + "00").substr(0, 2);
        }
        return BigInt(preComma + postComma);
    }

    function setURLParam(param, value, state, push = false) {
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set(param, value);
        const newUrl = `${window.location.origin}${window.location.pathname}?${urlParams.toString()}`;
        if (push) {
            history.pushState(state, newUrl, newUrl);
        } else {
            history.replaceState(state, newUrl, newUrl)
        }
        return newUrl;
    }

    function setEuroParam(euroVal) {
        setURLParam("euro", euroVal, euroVal, false);
    }

    function updateOutput() {
        output.value = (
            fields[0].value + " Euro, das sind ja "
            + fields[1].value + " Mark; "
            + fields[2].value + " Ostmark und "
            + fields[3].value + " Ostmark auf dem Schwarzmarkt!"
        );
    }

    function setAllFields(euroValue, ignored) {
        setEuroParam(getDisplayValue(euroValue));
        for (let i = 0; i < 4; i++) {
            const value = getDisplayValue(euroValue * factors[i]);
            fields[i].placeholder = value;
            if (i !== ignored) {
                fields[i].value = value;
            }
        }
    }

    function onSubmit() {
        for (const feld of fields) feld.value = getDisplayValue(feld.value);
        setEuroParam(fields[0].value);
        updateOutput();
    }

    for (let i = 0; i < 4; i++) {
        fields[i].oninput = function () {
            // remove "invalid" class
            for (const field of fields) field.className = "";
            // add "invalid" class if input is not a number
            if (!numberRegex.test(fields[i].value)) {
                fields[i].className = "invalid";
                return;
            }
            // parse input as it is a number
            setAllFields(strToBigInt(fields[i].value) / factors[i], i);
            // update the output
            updateOutput();
        }
    }
    // set the value of the fields to the placeholder set by tornado
    for (const field of fields) field.value = field.placeholder;
    // fix form submit
    const form = document.getElementById("form");
    form.action = "javascript:void(0)";
    form.onsubmit = () => onSubmit();
})();
// @license-end
