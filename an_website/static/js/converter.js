// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const output = document.getElementById("output");
const submitButton = document.getElementById("submit");

const fields = [
    document.getElementById("euro"),
    document.getElementById("mark"),
    document.getElementById("ost"),
    document.getElementById("schwarz")
];

const factors = [
    1, //Euro
    2, //Deutsche Mark
    4, //Ostmark
    20 //Ostmark auf dem Schwarzmarkt
];

const regex = /^([1-9]\d*|0)([.,]\d{2})?$/;

function getDisplayValue(wert) {
    let str = wert.toString().replace(".", ",");
    if (regex.test(str)) {
        return str;
    }
    if (str.startsWith(",")) {
        return "0" + str;
    }
    if (str.endsWith(",")) {
        return str.slice(0, -1);
    }
    const split = str.split(",");
    if (split.length > 1) {
        return split[0] + "," + (split[1] + "00")
            .slice(0, 2).replace(/,00$/, "");
    }
    return str;
}

function setEuroParam(euroVal) {
    setURLParam("euro", euroVal, euroVal, false);
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

function updateOutput() {
    output.value = (
        fields[0].value + " Euro, das sind ja "
        + fields[1].value + " Mark; "
        + fields[2].value + " Ostmark und "
        + fields[3].value + " Ostmark auf dem Schwarzmarkt!"
    );
}

function setAllFields(euroValue, ignored) {
    setEuroParam(euroValue.toString().replace(".", ","));
    for (let i = 0; i < 4; i++) {
        const value = getDisplayValue(euroValue * factors[i]);
        fields[i].placeholder = value;
        if (i !== ignored) {
            fields[i].value = value;
        }
    }
    updateOutput();
}

function onSubmit() {
    for (const feld of fields) {
        feld.value = getDisplayValue(
            Number.parseFloat(
                feld.value.replace(",", ".")
            )
        );
    }
    setEuroParam(fields[0].value);
    updateOutput();
}

for (let i = 0; i < 4; i++) {
    fields[i].oninput = function () {
        let val = fields[i].value.replace(",", ".");
        if (!isNaN(val)) { //if it is not Not a Number
            setAllFields(val / factors[i], i);
        }
    }
}
// set the value of the fields to
for (let i = 0; i < 4; i++) {
    fields[i].value = fields[i].placeholder;
}
// disable submit button
document.getElementById("form").action = "javascript:onSubmit()";
// @license-end
