// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import{get as l,PopStateHandlers as a,setURLParam as c}from"../utils/utils.js";var n=document.getElementById("search-results"),o=document.getElementById("search-form"),s=document.getElementById("search-input");function u(t){n.innerHTML="";for(let e of t){let r=document.createElement("li");r.setAttribute("score",String(e.score)),r.innerHTML="<a href='".concat(e.url,"'>")+"".concat(e.title,"</a> ").concat(e.description),n.appendChild(r)}}a.search=t=>{let e=t.state;s.value=e.query,u(e.results)},o.onsubmit=t=>(t.preventDefault(),l("/api/suche","q="+s.value,e=>{u(e),c("q",s.value,{query:s.value,results:e},"search",!0)}));
// @license-end
//# sourceMappingURL=search.js.map
