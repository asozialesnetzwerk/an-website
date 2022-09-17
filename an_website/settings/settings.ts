// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
"use strict";

function createBumpscositySlider() {
    const select = elById("bumpscosity-select") as HTMLSelectElement;

    if (!select) {
        return;
    }

    select.classList.add("hidden");
    const possibleLevels: number[] = [];
    for (const node of select.options) {
        possibleLevels.push(parseInt(node.value));
    }

    const startLevel = parseInt(select.value);

    const currentValueDiv = document.createElement("div");
    currentValueDiv.setAttribute("tooltip", startLevel.toString());
    currentValueDiv.style.position = "absolute";
    currentValueDiv.style.transform = "translateX(-50%)";

    const rangeSlider = document.createElement("input");
    rangeSlider.setAttribute("type", "range");
    rangeSlider.setAttribute("min", "0");
    rangeSlider.setAttribute(
        "value",
        possibleLevels.indexOf(startLevel).toString(),
    );
    rangeSlider.setAttribute("max", (select.options.length - 1).toString());

    rangeSlider.onpointermove = () => {
        const value = possibleLevels[parseInt(rangeSlider.value)].toString();
        select.value = value;
        currentValueDiv.setAttribute("tooltip", value);
        currentValueDiv.classList.add("show-tooltip");
        currentValueDiv.style.left = (1 +
            (98 *
                parseInt(rangeSlider.value) /
                (select.options.length - 1)))
            .toString() + "%";
    };

    rangeSlider.onpointerleave = () =>
        currentValueDiv.classList.remove("show-tooltip");

    rangeSlider.onchange = () => {
        let sliderVal = parseInt(rangeSlider.value);
        const promptStart = `Willst du die Bumpscosity wirklich auf ${
            possibleLevels[sliderVal]
        } setzen? `;
        if (sliderVal === select.options.length - 1) {
            if (
                !confirm(
                    promptStart +
                        "Ein so hoher Wert kann katastrophale Folgen haben.",
                )
            ) {
                sliderVal--;
            }
        } else if (sliderVal === 0) {
            if (
                !confirm(
                    promptStart +
                        "Fehlende Bumpscosity kann großes Unbehagen verursachen.",
                )
            ) {
                sliderVal++;
            }
        } else {
            return;
        }

        if (sliderVal !== parseInt(rangeSlider.value)) {
            rangeSlider.value = sliderVal.toString();
            select.value = possibleLevels[parseInt(rangeSlider.value)]
                .toString();
        }
    };

    const parent = select.parentElement as HTMLElement;
    parent.style.position = "relative";
    parent.append(currentValueDiv);
    parent.append(rangeSlider);
}

createBumpscositySlider();
// @license-end
