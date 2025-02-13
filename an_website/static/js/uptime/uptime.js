// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var o="uptime",m=()=>performance.now()/1e3,e=Math.floor,p=()=>{let t=document.getElementById(o);t.style.fontFamily="clock-face,monospace";let r=m()-Number(t.getAttribute(o)),s=()=>{let n=e(m()-r),c=e(n/60),i=e(c/60);t.innerText=[i/24,i%24,c%60,n%60].map(a=>(""+e(a)).padStart(2,"0")).join(":"),t.setAttribute(o,n)};s(),setInterval(s,1e3)};p();
// @license-end
//# sourceMappingURL=uptime.js.map
