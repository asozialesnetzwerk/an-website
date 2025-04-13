// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
function createBumpscositySlider() {
    const select = document.getElementById(
        "bumpscosity-select",
    ) as HTMLSelectElement | undefined;

    if (!select) {
        return;
    }

    select.classList.add("hidden");
    select.setAttribute("aria-hidden", "true");

    const possibleLevels: number[] = [...select.options]
        .map((node) => parseInt(node.value));
    const startLevel = parseInt(select.value);

    const currentValueDiv = (
        <div
            tooltip={startLevel.toString()}
            style="position: absolute; translateX(-50%)"
            aria-hidden="true"
        />
    ) as HTMLDivElement;

    const showTooltip = () => {
        currentValueDiv.classList.add("show-tooltip");
    };
    const hideTooltip = () => {
        currentValueDiv.classList.remove("show-tooltip");
    };
    const updateSelectAndTooltip = () => {
        const value = possibleLevels[parseInt(rangeSlider.value)]?.toString() ??
            "50";
        select.value = value;
        currentValueDiv.setAttribute("tooltip", value);
        currentValueDiv.style.left = (1 +
            (98 *
                parseInt(rangeSlider.value) /
                (possibleLevels.length - 1)))
            .toString() + "%";
    };

    const rangeSlider = (
        <input
            type="range"
            min="0"
            id={"bumpscosity-slider"}
            max={(possibleLevels.length - 1).toString()}
            value={possibleLevels.indexOf(startLevel).toString()}
            onpointermove={() => {
                showTooltip();
                updateSelectAndTooltip();
            }}
            onpointerleave={hideTooltip}
            onfocusin={showTooltip}
            onblur={hideTooltip}
            aria-valuetext={select.value}
            aria-valuemin={possibleLevels[0]!.toString()}
            aria-valuemax={possibleLevels[possibleLevels.length - 1]!
                .toString()}
            onchange={() => {
                let sliderVal = parseInt(rangeSlider.value);
                const promptStart = `Willst du die Bumpscosity wirklich auf ${
                    possibleLevels[sliderVal]
                } setzen? `;
                if (sliderVal === possibleLevels.length - 1) {
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
                }

                rangeSlider.value = sliderVal.toString();
                updateSelectAndTooltip();
                rangeSlider.setAttribute("aria-valuetext", select.value);
            }}
        />
    ) as HTMLInputElement;

    const parent = select.parentElement!;
    parent.style.position = "relative";
    parent.append(<>{currentValueDiv}{rangeSlider}</>);

    rangeSlider.parentElement!.setAttribute("for", rangeSlider.id);

    updateSelectAndTooltip();
}

createBumpscositySlider();
