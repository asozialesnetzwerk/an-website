import{d as o,e as a,get as h,hideSitePane as d,PopStateHandlers as p,setLastLocation as y}from"/static/js/utils/utils.js?v=113eb828cd027c5e";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var i=a("main"),u={},c=[];function f(t,e){if(!t){console.error("No data received");return}if(t.redirect){location.href=t.redirect;return}let n=t.url;if(!n){console.error("No URL in data ",t);return}if(!e){if(c.length===1&&c[0]===n)return;history.pushState({data:t,url:n,stateType:"dynLoad"},t.title,n),y(n)}if(!t.body){location.reload();return}if(o.onkeydown=()=>{},i.innerHTML=t.body,t.css){let r=o.createElement("style");r.innerHTML=t.css,i.appendChild(r)}for(let r of t.stylesheets){let s=o.createElement("link");s.rel="stylesheet",s.type="text/css",s.href=r,i.appendChild(s)}for(let r of t.scripts)if(r.src){let s=o.createElement("script");s.type=r.type,s.src=r.src,i.appendChild(s)}else console.error("Script without src",r);d(),o.title=t.title;let l=a("title");return l&&(l.setAttribute("short_title",t.short_title||t.title),l.innerText=t.title),u=t,!0}function L(t){return history.replaceState({data:u,url:location.href,scrollPos:[o.documentElement.scrollLeft||o.body.scrollLeft,o.documentElement.scrollTop||o.body.scrollTop],stateType:"dynLoad"},o.title,location.href),g(t)}async function g(t,e=!1){if(!e&&t===location.href){d();return}i.prepend("Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu."),await h(t,"",n=>f(n,!1),n=>{t===location.href?location.reload():location.href=t},"application/vnd.asozial.dynload+json")}async function m(t){if(t.state){let e=t.state;if(t.state.data&&f(e,!0)||await g(e.url||location.href,!0),e.scrollPos){scrollTo(e.scrollPos[0],e.scrollPos[1]);return}}console.error("Couldn't handle state.",t.state),location.reload()}p.dynLoad=m;o.addEventListener("click",t=>{var l;let e=(l=t.target)==null?void 0:l.closest("a");if(t.target,!e||e.target==="_blank"||e.hasAttribute("no-dynload"))return;let n=(e.href.startsWith("/")?location.origin:"")+e.href;n.startsWith("#")||n.startsWith("".concat(location.href.split("#")[0],"#"))||!n.startsWith(location.origin)||(t.preventDefault(),L(n).then(()=>{e.blur()}))});
// @license-end
//# sourceMappingURL=dynload.js.map
