import{Fragment as m,jsx as d,jsxs as h}from"/static/js/utils/utils.js?v=113eb828cd027c5e";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
function v(){let t=document.getElementById("bumpscosity-select");if(!t)return;t.classList.add("hidden");let n=[...t.options].map(e=>parseInt(e.value)),a=parseInt(t.value),o=d("div",{tooltip:a.toString(),style:"position: absolute; translateX(-50%)"}),r=()=>{o.classList.add("show-tooltip")},p=()=>{o.classList.remove("show-tooltip")},i=()=>{var l,u;let e=(u=(l=n[parseInt(s.value)])==null?void 0:l.toString())!=null?u:"50";t.value=e,o.setAttribute("tooltip",e),o.style.left=(1+98*parseInt(s.value)/(n.length-1)).toString()+"%"},s=d("input",{type:"range",min:"0",max:(n.length-1).toString(),value:n.indexOf(a).toString(),onpointermove:()=>{r(),i()},onpointerleave:p,onfocusin:r,onblur:p,onchange:()=>{let e=parseInt(s.value),l="Willst du die Bumpscosity wirklich auf ".concat(n[e]," setzen? ");e===n.length-1?confirm(l+"Ein so hoher Wert kann katastrophale Folgen haben.")||e--:e===0&&(confirm(l+"Fehlende Bumpscosity kann großes Unbehagen verursachen.")||e++),s.value=e.toString(),i()}}),c=t.parentElement;c.style.position="relative",c.append(h(m,{children:[o,s]})),i()}v();
// @license-end
//# sourceMappingURL=settings.js.map
