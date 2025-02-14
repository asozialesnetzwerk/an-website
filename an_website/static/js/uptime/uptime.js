// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var o="uptime",c=()=>performance.now()/1e3,n=Math.floor,p=()=>{let t=document.getElementById(o);t.style.fontFamily="clock-face,monospace";let r=c()-Number(t.getAttribute(o)),s=()=>{let e=n(c()-r),i=n(e/60),a=n(i/60);t.innerText=[a/24,a%24,i%60,e%60].map(m=>(n(m)+"").padStart(2,"0")).join(":"),t.setAttribute(o,e)};s(),setInterval(s,1e3)};p();
// @license-end
//# sourceMappingURL=uptime.js.map
