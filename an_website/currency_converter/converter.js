// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
(() => {
    let bigIntType = "bigint";
    try {
        BigInt(69);
    } catch (e) {
        // fix for cool browsers like Pale Moon that don't support BigInt
        BigInt = Number;
        bigIntType = "number";
    }
    const output = elById("output");

    const fields = [
        elById("euro"),
        elById("mark"),
        elById("ost"),
        elById("schwarz")
    ];
    const factors = [
        BigInt(1), //Euro
        BigInt(2), //Deutsche Mark
        BigInt(4), //Ostmark
        BigInt(20) //Ostmark auf dem Schwarzmarkt
    ];

    const numberRegex = /^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/;

    function getDisplayValue(wert) {
        if (typeof wert === "string") {
            wert = strToBigInt(wert);
        }
        if (typeof wert !== bigIntType) {
            alert(`Ungültiger Wert ${wert} mit type ${typeof wert}`);
        }
        if (bigIntType === "number") {
            wert = Math.floor(wert);
        }
        let str = wert.toString();
        if (bigIntType === "number" && str.includes("e")) {
            let [num, pow] = str.split("e");
            if (pow.startsWith("-")) {
                // too small to be displayed
                str = "0";
            } else {
                let [int, dec] = num.split(".");
                if (!dec) {
                    dec = "";
                }
                pow = Number(pow);
                str = int + dec + "0".repeat(pow - dec.length);
            }
        }
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
            return BigInt(0);
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
            // get the first two digits after the comma, fill with 0 if needed
            postComma = (postComma + "00").slice(0, 2);
        }
        return BigInt(preComma + postComma);
    }

    w.PopStateHandlers["currencyConverter"] = function (state) {
        if (state.input) {
            fields.forEach((field, i) => {
                field.value = getDisplayValue(state.input[i]);
            });
        }
    };

    w.PopStateHandlers["currencyConverter"] = (event) => {
        setAllFields(strToBigInt(event.state["euro"]));
    };
    function setEuroParam(euroVal, push) {
        setURLParam(
            "euro",
            euroVal,
            {"euro": euroVal},
            "currencyConverter",
            push
        );
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
        setEuroParam(getDisplayValue(euroValue), false);
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
        setEuroParam(fields[0].value, true);
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
    const form = elById("form");
    form.action = "javascript:void(0)";
    form.onsubmit = () => onSubmit();
})();
// @license-end
