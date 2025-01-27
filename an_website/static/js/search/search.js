// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import{get as a,PopStateHandlers as i,setURLParam as c,e as n,d as o}from"/static/js/utils/utils.js?v=28e0afd522a7348b";var u=n("search-results"),m=n("search-form"),s=n("search-input");function l(t){u.innerHTML="";for(let e of t){let r=o.createElement("li");r.setAttribute("score",String(e.score)),r.innerHTML="<a href='".concat(e.url,"'>")+"".concat(e.title,"</a> ").concat(e.description),u.appendChild(r)}}i.search=t=>{let e=t.state;s.value=e.query,l(e.results)},m.onsubmit=t=>(t.preventDefault(),a("/api/suche","q="+s.value,e=>{l(e),c("q",s.value,{query:s.value,results:e},"search",!0)}));
// @license-end
//# sourceMappingURL=search.js.map
