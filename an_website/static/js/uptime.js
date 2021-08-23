const uptimeDiv = document.getElementById("uptime");
// uptimeAtStart is set in the html document
// the time the website got loaded minus the uptime
const startTime = Date.now()/1000 - uptimeAtStart;

function displayUptime() {
    // the uptime: currentTime - (startTime - uptime at start)
    //             time on website          + uptime at start
    const uptime = Math.floor(Date.now()/1000 - startTime);
    // display uptime:
    const div_60 = Math.floor(uptime / 60);
    const div_60_60 = Math.floor(div_60 / 60);

    const seconds = uptime % 60;
    const minutes = div_60 % 60;
    const hours = div_60_60 % 24;
    const days = Math.floor(div_60_60 / 24);

    uptimeDiv.innerText = `${days}d ${hours}h ${minutes}min ${seconds}s`;
}
displayUptime();
setInterval(displayUptime, 1000);