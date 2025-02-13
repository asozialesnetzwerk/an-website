// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
export {};

const UPTIME_STRING = "uptime" as const;

const currentTimeInSeconds = () => (performance.now() / 1000);
const floor = Math.floor;

const startDisplayingUptime = () => {
    const uptimeDiv = document.getElementById(UPTIME_STRING) as HTMLDivElement;
    // set the font family, because it looks much better
    uptimeDiv.style.fontFamily = "clock-face,monospace";
    // the time the website got loaded minus the uptime
    const startTime = currentTimeInSeconds() - Number(
        uptimeDiv.getAttribute(UPTIME_STRING)!,
    );

    const displayUptime = () => {
        // the uptime: currentTime - (startTime - uptime at start)
        //             time on website          + uptime at start
        const uptime = floor(currentTimeInSeconds() - startTime);
        // display uptime:
        const div_60 = floor(uptime / 60);
        const div_60_60 = floor(div_60 / 60);
        uptimeDiv.innerText = [
            div_60_60 / 24, // days
            div_60_60 % 24, // hours
            div_60 % 60, // minutes
            uptime % 60, // seconds
        ]
            .map((n: number) => ("" + floor(n)).padStart(2, "0"))
            .join(":");
        uptimeDiv.setAttribute(UPTIME_STRING, uptime);
    };

    displayUptime();
    setInterval(displayUptime, 1000);
};

startDisplayingUptime();
