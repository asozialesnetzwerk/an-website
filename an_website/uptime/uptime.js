// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
function startDisplayingUptime(uptimeAtStart) {
    const uptimeDiv = elById("uptime");
    // set the font family, because it looks much better
    uptimeDiv.style.fontFamily = "'clock-face', monospace";
    // the time the website got loaded minus the uptime
    const startTime = (performance.now() / 1000) - uptimeAtStart;

    const zeroPad = n => String(Math.floor(n)).padStart(2, "0");

    const displayUptime = () => {
        // the uptime: currentTime - (startTime - uptime at start)
        //             time on website          + uptime at start
        const uptime = Math.floor((performance.now() / 1000) - startTime);
        // display uptime:
        const div_60 = Math.floor(uptime / 60);
        const div_60_60 = Math.floor(div_60 / 60);
        uptimeDiv.innerText = [
            zeroPad(div_60_60 / 24), // days
            zeroPad(div_60_60 % 24),  // hours
            zeroPad(div_60 % 60),  // minutes
            zeroPad(uptime % 60)  // seconds
        ].join(":");
    };

    displayUptime();
    setInterval(displayUptime, 1000);
}
// @license-end
