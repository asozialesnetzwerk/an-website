import{e as r,PopStateHandlers as u,post as a}from"/static/js/utils/utils.js?v=a5509821140bb048";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var i=r("text"),l=r("config-textarea"),f=r("output"),n=r("error-msg");n.innerHTML.trim()&&alert(n.innerHTML.trim());function o(e,t=!1){if(e){if(e.error){s(e);return}t||(e.stateType="swappedWords",history.pushState(e,"Vertauschte Wörter",location.href)),i.value=e.text||"",l.value=e.config||"",f.innerText=e.replaced_text||"",n.innerText=""}}function s(e){let t=e;console.error(t),t.error?(alert(t.error),n.innerText="".concat(t.error," In line ").concat(t.line_num,': "').concat(t.line,'"')):(alert(t),n.innerText=JSON.stringify(t))}r("form").onsubmit=e=>{e.preventDefault()};r("reset").onclick=()=>a("/api/vertauschte-woerter",{text:i.value,minify_config:!1,return_config:!0},o,s);r("submit").onclick=()=>a("/api/vertauschte-woerter",{text:i.value||"",config:l.value||"",minify_config:!1,return_config:!0},o,s);u.swappedWords=e=>{e.state&&o(e.state,!0)};
// @license-end
//# sourceMappingURL=swap.js.map
