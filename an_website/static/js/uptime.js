// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
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
    uptimeDiv.innerText = (
      `${Math.floor(div_60_60 / 24)}d ${div_60_60 % 24}h `
      + `${div_60 % 60}min ${uptime % 60}s`
    );
}
displayUptime();
setInterval(displayUptime, 1000);

// @license-end
