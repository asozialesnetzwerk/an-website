// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
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
        elById("euro"),   // Euro
        elById("mark"),   // Deutsche Mark
        elById("ost"),    // Ostmark
        elById("schwarz") // Ostmark auf dem Schwarzmarkt
    ];
    const factors = [
        BigInt(1), // Euro
        BigInt(2), // Deutsche Mark
        BigInt(4), // Ostmark
        BigInt(20) // Ostmark auf dem Schwarzmarkt
    ];
    const numberRegex = /^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/;

    const isZero = (str) => /^0*$/.test(str);

    function getDisplayValue(wert) {
        if (typeof wert === "string")
            wert = strToBigInt(wert);

        if (typeof wert !== bigIntType)
            alert(`Ungültiger Wert ${wert} mit type ${typeof wert}`);

        if (bigIntType === "number") wert = Math.floor(wert);

        let str = wert.toString();
        if (bigIntType === "number" && str.includes("e")) {
            let [num, pow] = str.split("e");

            if (pow.startsWith("-")) return "0"; // too small to be displayed

            let [int, dec] = num.split(".");
            dec = dec || "";
            str = int + dec + "0".repeat(pow - dec.length);
        }
        if (isZero(str)) return "0";  // is empty string or 0

        let dec = str.slice(-2);  // last two chars or whole str if len <= 2
        return (
            (str.slice(0, -2) || "0")  // integer part, but "0" instead of ""
            + (
                isZero(dec)
                    ? ""  // if is integer do not append
                    : "," + (dec.length === 1 ? "0" : "") + dec
            )
        );
    }

    function strToBigInt(str) {
        if (typeof str !== "string") throw `${str} is not a String.`;

        if (isZero(str)) return BigInt(0);

        let [int, dec] = [str, "00"];
        if (str.includes(",")) {
            [int, dec] = str.split(",");
        } else if (str.includes(".")) {
            [int, dec] = str.split(".");
        }
        if (dec.length !== 2) {
            // get the first two digits after the comma, fill with 0 if needed
            dec = (dec + "00").slice(0, 2);
        }
        return BigInt(int + dec);
    }

    w.PopStateHandlers["currencyConverter"] = (e) => setAllFields(
        strToBigInt(e.state["euro"])
    );

    const setEuroParam = (euroVal, push) => setURLParam(
        "euro",
        euroVal,
        {"euro": euroVal},
        "currencyConverter",
        push
    );

    function setAllFields(euroValue, ignored) {
        setEuroParam(getDisplayValue(euroValue), false);
        for (let i = 0; i < 4; i++) {
            const value = getDisplayValue(euroValue * factors[i]);
            fields[i].placeholder = value;
            if (i !== ignored) fields[i].value = value;
        }
    }

    const updateOutput = () => {
        output.value = (
            fields[0].value + " Euro, das sind ja "
            + fields[1].value + " Mark; "
            + fields[2].value + " Ostmark und "
            + fields[3].value + " Ostmark auf dem Schwarzmarkt!"
        );
    }

    function onSubmit() {
        for (const feld of fields)
            feld.value = getDisplayValue(feld.value);
        setEuroParam(fields[0].value, true);
        updateOutput();
    }

    for (let i = 0; i < 4; i++) {
        fields[i].oninput = () => {
            // remove "invalid" class
            for (const field of fields) field.className = "";
            // add "invalid" class if input is not a number
            if (!numberRegex.test(fields[i].value)) {
                fields[i].className = "invalid";
                return;
            }
            // parse input as it is a number
            setAllFields(strToBigInt(fields[i].value) / factors[i], i);

            updateOutput();
        }
    }
    // set the value of the fields to the placeholder set by tornado
    for (const field of fields)
        field.value = field.placeholder;
    // fix form submit
    const form = elById("form");
    form.action = "javascript:void(0)";
    form.onsubmit = () => onSubmit();
})();
// @license-end
