import{Fragment as u,jsx as r,jsxs as c}from"/static/js/utils/jsx-runtime.js?v=52bda3d0fbdde8d8";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
function p(){let t=document.getElementById("bumpscosity-select");if(!t)return;t.classList.add("hidden");let n=[...t.options].map(e=>parseInt(e.value)),l=parseInt(t.value),a=r("div",{tooltip:l.toString(),style:"position: absolute; translateX(-50%)"}),s=r("input",{type:"range",min:"0",max:(n.length-1).toString(),value:n.indexOf(l).toString(),onpointermove:()=>{let e=n[parseInt(s.value)].toString();t.value=e,a.setAttribute("tooltip",e),a.classList.add("show-tooltip"),a.style.left=(1+98*parseInt(s.value)/(n.length-1)).toString()+"%"},onpointerleave:()=>{a.classList.remove("show-tooltip")},onchange:()=>{let e=parseInt(s.value),i="Willst du die Bumpscosity wirklich auf ".concat(n[e]," setzen? ");if(e===n.length-1)confirm(i+"Ein so hoher Wert kann katastrophale Folgen haben.")||e--;else if(e===0)confirm(i+"Fehlende Bumpscosity kann großes Unbehagen verursachen.")||e++;else return;e!==parseInt(s.value)&&(s.value=e.toString(),t.value=n[parseInt(s.value)].toString())}}),o=t.parentElement;o.style.position="relative",o.append(c(u,{children:[a,s]}))}p();
// @license-end
//# sourceMappingURL=settings.js.map
