const snow = document.getElementById("snow");

let snowflakesCount = 200;

let bodyHeightPx = null;
let pageHeightVh = null;

function setHeightVariables() {
    bodyHeightPx = document.body.parentElement.getBoundingClientRect().height;
    pageHeightVh = 100 * Math.max(bodyHeightPx / window.innerHeight, 1);
}

function getSnowAttributes() {
    if (snow) {
        snowflakesCount = Number(
            snow.attributes?.count?.value || snowflakesCount,
        );
    }
}

// This function allows you to turn the snow on and off
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function showSnow(value) {
    if (value) {
        snow.style.display = "block";
    } else {
        snow.style.display = "none";
    }
}

// Creating snowflakes
function spawnSnow(snowDensity = 200) {
    for (let i = 1; i <= snowDensity; i++) {
        const flake = document.createElement("p");
        snow.appendChild(flake);
    }
}

// Append style for each snowflake to the head
function addCss(rule) {
    const css = document.createElement("style");
    css.appendChild(document.createTextNode(rule)); // Support for the rest
    document.getElementsByTagName("head")[0].appendChild(css);
}

// Math
function randomInt(value = 100) {
    return Math.floor(Math.random() * value) + 1;
}

function randomIntRange(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomArbitrary(min, max) {
    return Math.random() * (max - min) + min;
}

// Create style for snowflake
function spawnSnowCSS(snowDensity = 200) {
    let rule = "";

    for (let i = 1; i <= snowDensity; i++) {
        const randomX = Math.random() * 100; // vw
        const randomOffset = Math.random() * 10; // vw
        const randomXEnd = randomX + randomOffset;
        const randomXEndYoyo = randomX + (randomOffset / 2);
        const randomYoyoTime = getRandomArbitrary(0.3, 0.8);
        const randomYoyoY = randomYoyoTime * pageHeightVh; // vh
        const randomScale = Math.random();
        const fallDuration = randomIntRange(10, pageHeightVh / 10 * 3); // s
        const fallDelay = randomInt(pageHeightVh / 10 * 3) * -1; // s
        const opacity = Math.random();

        rule += `
      #snow p:nth-child(${i}) {
        opacity: ${opacity};
        transform: translate(${randomX}vw, -10px) scale(${randomScale});
        animation: fall-${i} ${fallDuration}s ${fallDelay}s linear infinite;
      }
      @keyframes fall-${i} {
        ${randomYoyoTime * 100}% {
          transform: translate(${randomXEnd}vw, ${randomYoyoY}vh) scale(${randomScale});
        }
        to {
          transform: translate(${randomXEndYoyo}vw, ${pageHeightVh}vh) scale(${randomScale});
        }
      }
    `;
    }
    addCss(rule);
}

// Load the rules and execute after the DOM loads
function createSnow() {
    setHeightVariables();
    getSnowAttributes();
    spawnSnowCSS(snowflakesCount);
    if (!snow.firstElementChild) {
        spawnSnow(snowflakesCount);
    }
}

window.onload = createSnow;

// TODO add option to easily re-render scenery. For example when window resizes.
// this should be easy as CSS rerenders after display block -> none -> block;
// TODO add progress bar for slower clients
