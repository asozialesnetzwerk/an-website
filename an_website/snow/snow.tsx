// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
const snow = document.getElementById("snow") as HTMLDivElement;
/* eslint-disable @typescript-eslint/no-unused-vars */

let snowflakesCount = 200;

let bodyHeightPx: number;
let pageHeightVh: number;

function setHeightVariables(): void {
    bodyHeightPx = document.documentElement.getBoundingClientRect().height;
    pageHeightVh = 100 * Math.max(bodyHeightPx / innerHeight, 1);
}

function getSnowAttributes(): void {
    snowflakesCount = Number(
        // @ts-expect-error TS2339
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
        snow.attributes.count?.value ?? snowflakesCount,
    );
}

// This function allows you to turn the snow on and off
export function showSnow(value: boolean): void {
    if (value) {
        snow.style.display = "block";
    } else {
        snow.style.display = "none";
    }
}

// Creating snowflakes
function spawnSnow(snowDensity = 200): void {
    for (let i = 1; i <= snowDensity; i++) {
        snow.append(<p />);
    }
}

// Append style for each snowflake to the head
function addCss(rules: string[]): void {
    document.querySelector("head")!.append(
        <style>{rules}</style>,
    );
}

// Math
function randomInt(value = 100): number {
    return Math.floor(Math.random() * value) + 1;
}

function randomIntRange(min: number, max: number): number {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomArbitrary(min: number, max: number): number {
    return Math.random() * (max - min) + min;
}

// Create style for snowflake
function spawnSnowCSS(snowDensity = 200): void {
    const rule: string[] = [];

    for (let i = 1; i <= snowDensity; i++) {
        const randomX = Math.random() * 100; // vw
        const randomOffset = Math.random() * 10; // vw
        const randomXEnd = randomX + randomOffset;
        const randomXEndYoyo = randomX + (randomOffset / 2);
        const randomYoyoTime = getRandomArbitrary(0.3, 0.8);
        const randomYoyoY = randomYoyoTime * 100; // vh
        const randomScale = Math.random();
        const fallDuration = randomIntRange(10, 30); // s
        const fallDelay = randomInt(30) * -1; // s
        const opacity = Math.random();

        rule.push(
            `#snow p:nth-child(${i}){opacity:${opacity};transform:translate(${randomX}vw,-10px) scale(${randomScale});animation:fall-${i} ${fallDuration}s ${fallDelay}s linear infinite}@keyframes fall-${i}{${
                randomYoyoTime * 100
            }%{transform:translate(${randomXEnd}vw,${randomYoyoY}vh) scale(${randomScale})}to{transform:translate(${randomXEndYoyo}vw,100vh) scale(${randomScale})}}`,
        );
    }

    addCss(rule);
}

// Load the rules and execute after the DOM loads
export function createSnow(): void {
    // setHeightVariables();
    // getSnowAttributes();
    spawnSnowCSS(snowflakesCount);
    // if (!snow.firstElementChild) {
    //     spawnSnow(snowflakesCount);
    // }
}

// TODO add option to easily re-render scenery. For example when window resizes.
// this should be easy as CSS rerenders after display block -> none -> block;
// TODO add progress bar for slower clients
