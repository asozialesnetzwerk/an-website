"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(()=>{const a=elById("search-results"),l=elById("search-form"),s=elById("search-input");function n(t){a.innerHTML="";for(const e of t){const r=document.createElement("li");r.setAttribute("score",String(e.score)),r.innerHTML=`<a href='${e.url}'>${e.title}</a> ${e.description}`,a.appendChild(r)}}PopStateHandlers.search=t=>{s.value=t.state.query,n(t.state.results)},l.onsubmit=t=>{t.preventDefault(),get("/api/suche","q="+s.value,e=>{n(e),setURLParam("q",s.value,{query:s.value,results:e},"search",!0)})}})();// @license-end
//# sourceMappingURL=search.js.map