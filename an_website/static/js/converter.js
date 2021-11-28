// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const output = document.getElementById("output");
const submitButton = document.getElementById("submit");

const felder = [
    document.getElementById("euro"),
    document.getElementById("mark"),
    document.getElementById("ost"),
    document.getElementById("schwarz")
];

const multiplikator = [
    1, //Euro
    2, //Deutsche Mark
    4, //Ostmark
    20 //Ostmark auf dem Schwarzmarkt
];

const regex = /^([1-9]\d*|0)([.,]\d{2})?$/;

function bekommeAnzeigeWert(wert) {
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

function setEuroParam(euroWert) {
    let url = window.location.href;
    const end = url.lastIndexOf("?");
    url = url.slice(0, end === -1 ? url.length : end) + "?euro=" + euroWert;
    history.replaceState("", url, url);
}

function setzeAlleFelder (euroWert, ignoriert) {
    setEuroParam(euroWert.toString().replace(".", ","));
    for (let i = 0; i < 4; i++) {
        const wert = bekommeAnzeigeWert(euroWert * multiplikator[i]);
        felder[i].placeholder = wert;
        if (i !== ignoriert) {
            felder[i].classList.remove("fehler");
            felder[i].value = wert;
        }
    }
    updateOutput();
}

function updateOutput() {
    output.value = (
        felder[0].value + " Euro, das sind ja "
        + felder[1].value + " Mark; "
        + felder[2].value + " Ostmark und "
        + felder[3].value + " Ostmark auf dem Schwarzmarkt!"
    );
}

for (let i = 0; i < 4; i++) {
    felder[i].oninput = function () {
        let val = felder[i].value.replace(",", ".");
        if (!isNaN(val)) { //if it is not Not a Number
            setzeAlleFelder(val / multiplikator[i], i);
        }
    }
}
// set the value of the fiels to
for (let i = 0; i < 4; i++) {
    felder[i].value = felder[i].placeholder;
}
// disable submit button
document.getElementById("form").action = "javascript:void(0)";
// fix the values in the inputs to look better
submitButton.onclick = () => {
    for (const feld of felder) {
        feld.value = bekommeAnzeigeWert(Number.parseInt(feld.value));
    }
    updateOutput();
}
// @license-end
