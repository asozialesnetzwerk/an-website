// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import{d as s,e as a,get as p,hideSitePane as c,PopStateHandlers as g,setLastLocation as y}from"/static/js/utils/utils.js?v=28e0afd522a7348b";var l=a("main"),d={},f=[];function u(t,e){if(!t){console.error("No data received");return}if(t.redirect){location.href=t.redirect;return}let n=t.url;if(!n){console.error("No URL in data ",t);return}if(!e){if(f.length===1&&f[0]===n)return;history.pushState({data:t,url:n,stateType:"dynLoad"},t.title,n),y(n)}if(!t.body){location.reload();return}if(s.onkeydown=()=>{},l.innerHTML=t.body,t.css){let o=s.createElement("style");o.innerHTML=t.css,l.appendChild(o)}for(let o of t.stylesheets){let r=s.createElement("link");r.rel="stylesheet",r.type="text/css",r.href=o,l.appendChild(r)}for(let o of t.scripts)if(o.src){let r=s.createElement("script");r.type=o.type,r.src=o.src,l.appendChild(r)}else console.error("Script without src",o);c(),s.title=t.title;let i=a("title");return i&&(i.setAttribute("short_title",t.short_title||t.title),i.innerText=t.title),d=t,!0}function L(t){return history.replaceState({data:d,url:location.href,scrollPos:[s.documentElement.scrollLeft||s.body.scrollLeft,s.documentElement.scrollTop||s.body.scrollTop],stateType:"dynLoad"},s.title,location.href),h(t)}async function h(t,e=!1){if(!e&&t===location.href){c();return}l.prepend("Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu."),await p(t,"",n=>u(n,!1),n=>{t===location.href?location.reload():location.href=t},"application/vnd.asozial.dynload+json")}async function m(t){if(t.state){let e=t.state;if(t.state.data&&u(e,!0)||await h(e.url||location.href,!0),e.scrollPos){scrollTo(e.scrollPos[0],e.scrollPos[1]);return}}console.error("Couldn't handle state.",t.state),location.reload()}g.dynLoad=m,s.addEventListener("click",t=>{var o,r;if(((o=t.target)==null?void 0:o.tagName)!=="A")return;let e=t.target;if(e.target==="_blank")return;let n=(e.href.startsWith("/")?location.origin+e.href:e.href).trim(),i=n.split("?")[0];!n.startsWith(location.origin)||((r=i.split("/").pop())!=null?r:"").includes(".")&&i!==location.origin+"/redirect"||i===location.origin+"/chat"||n.startsWith("#")||n.startsWith("".concat(location.href.split("#")[0],"#"))||(t.preventDefault(),L(n).then(()=>{e.blur()}))});
// @license-end
//# sourceMappingURL=dynload.js.map
