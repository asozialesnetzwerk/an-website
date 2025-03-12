// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var n={};for(let t of document.getElementById("quote-list").children)n[t.value.toLowerCase()]=t.attributes.getNamedItem("data-author").value;var e=document.getElementById("quote-input"),a=document.getElementById("real-author-input");e.oninput=()=>{let t=n[e.value.toLowerCase()];a.disabled=!!t,t&&(a.value=t)};
// @license-end
//# sourceMappingURL=create.js.map
