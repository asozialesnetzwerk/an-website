// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var e={};for(let t of document.getElementById("quote-list").children)e[t.value.toLowerCase()]=t.attributes.getNamedItem("data-author").value;var a=document.getElementById("quote-input"),n=document.getElementById("real-author-input");a.oninput=()=>{let t=e[a.value.toLowerCase()];n.disabled=!!t,t&&(n.value=t)};
// @license-end
//# sourceMappingURL=create.js.map
