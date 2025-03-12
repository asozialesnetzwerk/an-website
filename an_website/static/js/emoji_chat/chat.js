import{e as i}from"/static/js/utils/utils.js?v=53ffc47ed238b094";import{Fragment as S,jsx as s,jsxs as I}from"/static/js/utils/utils.js?v=53ffc47ed238b094";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var o=i("message-input"),y=o.form,f=i("message-section"),a=i("openmoji-attribution"),u=a==null?void 0:a.getAttribute("openmoji-version"),c=100,m=0,d="",E=e=>new Date(e+16510752e5).toLocaleString(),h=()=>a==null?void 0:a.getAttribute("type"),C=({emoji:e})=>{let t=[...e],n=(t.length==2&&t[1]==="️"?[t[0]]:t).map(k=>k.codePointAt(0).toString(16).padStart(4,"0")).join("-").toUpperCase(),p="/static/openmoji/svg/".concat(n,".svg");return s("img",{src:u?"".concat(p,"?v=").concat(u):p,alt:e,className:"emoji"})},g=({emoji:e})=>h()==="img"?s(C,{emoji:e}):e,j=({msg:e})=>I("div",{tooltip:E(e.timestamp),children:[s(S,{children:e.author.map(t=>s(g,{emoji:t}))}),": ",s(S,{children:e.content.map(t=>s(g,{emoji:t}))})]}),v=e=>{f.append(s(j,{msg:e}))},M=e=>{let t="current-user";i(t).replaceWith(s("div",{className:h()?"openmoji":"",id:t,children:e.map(n=>s(g,{emoji:n}))}))},b=()=>{d&&!o.value&&(o.value=d,d="")},$={connecting:"Versuche mit WebSocket zu verbinden",connected:"Mit WebSocket verbunden!",disconnected:"Verbindung getrennt. Drücke hier um erneut zu versuchen."},r=e=>{let t="connection-state",n=e=="disconnected"?()=>{m=0,c=500,i(t).removeEventListener("click",n),l()}:void 0;i(t).replaceWith(s("div",{tooltip:$[e],"tooltip-position":"right",onclick:n,"data-state":e,id:t}))},w=e=>{let t=JSON.parse(e.data);switch(t.type){case"messages":{f.innerText="";for(let n of t.messages)v(n);break}case"message":{v(t.message);break}case"init":{M(t.current_user),t.current_user.join(""),r("connected"),c=100,m=0;break}case"users":{t.users;break}case"ratelimit":{b(),alert("Retry after ".concat(t.retry_after," seconds."));break}case"error":{b(),alert(t.error);break}default:console.error("Invalid type ".concat(t.type))}},l=()=>{r("connecting");let e=new WebSocket((location.protocol==="https:"?"wss:":"ws:")+"//".concat(location.host,"/websocket/emoji-chat")),t=setInterval(()=>{e.readyState==e.OPEN&&e.send("")},1e4);e.addEventListener("close",n=>{if(clearInterval(t),n.wasClean){"Connection closed cleanly, code=".concat(n.code," reason=").concat(n.reason),r("disconnected");return}if("Connection closed, reconnecting in ".concat(c,"ms  (").concat(m,")"),r("connecting"),m>10){r("disconnected");return}setTimeout(()=>{c=Math.max(500,Math.floor(Math.min(15e3,1.5*c-200))),m++,l()},c)}),e.addEventListener("open",n=>{r("connected")}),e.addEventListener("error",n=>{console.error({msg:"got error from websocket",event:n})}),e.addEventListener("message",n=>{w(n)}),y.addEventListener("submit",n=>{o.value!==""&&(d=o.value,e.send(JSON.stringify({type:"message",message:o.value})),o.value=""),n.preventDefault()})};l();
// @license-end
//# sourceMappingURL=chat.js.map
