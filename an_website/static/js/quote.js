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
document.addEventListener("keydown", function(event) {
    if(event.code === "ArrowUp" || event.code === "KeyW") {
        document.getElementById("upvote").click();
    } else if(event.code === "ArrowLeft" || event.code === "KeyA") {
        window.history.go(-1);
    } else if(event.code === "ArrowDown" || event.code === "KeyS") {
        document.getElementById("downvote").click();
    } else if(event.code === "ArrowRight" || event.code === "KeyD") {
        document.getElementById("next").click();
    }
});
// @license-end
