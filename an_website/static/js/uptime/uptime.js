// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
export{};function s(){const e=document.getElementById("uptime");e.style.fontFamily="'clock-face', monospace";const a=performance.now()/1e3-parseFloat(e.getAttribute("uptime")),o=t=>String(Math.floor(t)).padStart(2,"0"),n=()=>{const t=Math.floor(performance.now()/1e3-a),i=Math.floor(t/60),r=Math.floor(i/60);e.innerText=[o(r/24),o(r%24),o(i%60),o(t%60)].join(":"),e.setAttribute("uptime",String(t))};n(),setInterval(n,1e3)}s();// @license-end
//# sourceMappingURL=uptime.js.map
