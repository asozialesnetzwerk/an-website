import{e as r,get as n,PopStateHandlers as l,setURLParam as u}from"/static/js/utils/utils.js?v=c676bb123f83b0ed";import{jsx as o,jsxs as p}from"/static/js/utils/utils.js?v=c676bb123f83b0ed";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var c=r("search-results"),i=r("search-form"),s=r("search-input");function a(t){c.replaceChildren(...t.map(e=>p("li",{"data-score":e.score,children:[o("a",{href:e.url,children:[e.title]}),": ",e.description]})))}l.search=t=>{let e=t.state;s.value=e.query,a(e.results)};i.onsubmit=t=>(t.preventDefault(),n("/api/suche","q="+s.value,e=>{a(e),u("q",s.value,{query:s.value,results:e},"search",!0)}));
// @license-end
//# sourceMappingURL=search.js.map
