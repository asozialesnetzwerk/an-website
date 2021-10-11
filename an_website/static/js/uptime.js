// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
/*
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/
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

// @license-end
