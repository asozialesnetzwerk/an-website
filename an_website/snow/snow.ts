// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
window.showSnow = (() => {
    const random = Math.random;
    const snow = document.getElementById("snow") as HTMLDivElement;

    const snowflakesCount = 200;

    // let bodyHeightPx: number;
    // let pageHeightVh: number;

    // function setHeightVariables(): void {
    //     bodyHeightPx = document.documentElement.getBoundingClientRect().height;
    //     pageHeightVh = 100 * Math.max(bodyHeightPx / window.innerHeight, 1);
    // }

    // function getSnowAttributes(): void {
    //     if (snow) {
    //         snowflakesCount = Number(
    //             // @ts-expect-error TS2339
    //             // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    //             snow.attributes?.count?.value ?? snowflakesCount,
    //         );
    //     }
    // }

    // Creating snowflakes
    // function spawnSnow(snowDensity = 200): void {
    //     for (let i = 1; i <= snowDensity; i++) {
    //         const flake = document.createElement("p");
    //         snow.appendChild(flake);
    //     }
    // }

    // Append style for each snowflake to the head
    function addCss(rule: string): void {
        const css = document.createElement("style");
        css.appendChild(document.createTextNode(rule)); // Support for the rest
        // @ts-expect-error TS2532
        document.getElementsByTagName("head")[0].appendChild(css);
    }

    // Math
    function randomInt(value = 100): number {
        return Math.floor(random() * value) + 1;
    }

    function randomIntRange(min: number, max: number): number {
        min = Math.ceil(min);
        max = Math.floor(max);
        return Math.floor(random() * (max - min + 1)) + min;
    }

    function getRandomArbitrary(min: number, max: number): number {
        return random() * (max - min) + min;
    }

    // Create style for snowflake
    function spawnSnowCSS(snowDensity = 200): void {
        const getTransform = (
            translateX: string,
            translateY: string,
            scale: number,
        ): string => {
            return `transform: translate(${translateX}, ${translateY}) scale(${scale});`;
        };

        let rule = "";

        for (let i = 1; i <= snowDensity; i++) {
            const randomX = random() * 100; // vw
            const randomOffset = random() * 10; // vw
            const randomXEnd = randomX + randomOffset;
            const randomXEndYoyo = randomX + (randomOffset / 2);
            const randomYoyoTime = getRandomArbitrary(0.3, 0.8) as number;
            const randomYoyoY = randomYoyoTime * 100; // vh
            const randomScale = random();
            const fallDuration = randomIntRange(10, 30) as number; // s
            const fallDelay = randomInt(30) * -1; // s

            rule += `
#snow p:nth-child(${i}) {
  opacity: ${random()};
  ${getTransform(randomX + "vw", "-10px", randomScale)}
  animation: fall-${i} ${fallDuration}s ${fallDelay}s linear infinite;
}
@keyframes fall-${i} {
  ${randomYoyoTime * 100}% {${
                getTransform(randomXEnd + "vw", randomYoyoY + "vh", randomScale)
            }}
  to {${getTransform(randomXEndYoyo + "vw", "100vh", randomScale)}}
}`;
        }
        addCss(rule);
    }

    // Load the rules and execute after the DOM loads
    function createSnow(): void {
        // setHeightVariables();
        // getSnowAttributes();
        spawnSnowCSS(snowflakesCount);
        // if (!snow.firstElementChild) {
        //     spawnSnow(snowflakesCount);
        // }
    }

    window.onload = createSnow;
    // TODO add option to easily re-render scenery. For example when window resizes.
    // this should be easy as CSS rerenders after display block -> none -> block;
    // TODO add progress bar for slower clients

    return (value: boolean): void => { // showSnow
        if (value) {
            snow.style.display = "block";
        } else {
            snow.style.display = "none";
        }
    };
})();
// @license-end
