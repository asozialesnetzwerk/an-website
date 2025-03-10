var C=Object.defineProperty;var v=Object.getOwnPropertySymbols;var M=Object.prototype.hasOwnProperty,j=Object.prototype.propertyIsEnumerable;var b=(t,e,n)=>e in t?C(t,e,{enumerable:!0,configurable:!0,writable:!0,value:n}):t[e]=n,S=(t,e)=>{for(var n in e||(e={}))M.call(e,n)&&b(t,n,e[n]);if(v)for(var n of v(e))j.call(e,n)&&b(t,n,e[n]);return t};import{jsx as o}from"/static/js/utils/jsx-runtime.js?v=c120d61e10a3b6c6";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import{e as a}from"/static/js/utils/utils.js?v=b4ed019200cc7b4b";var r=a("message-input"),L=r.form,f=a("message-section"),c=a("openmoji-attribution"),h=c==null?void 0:c.getAttribute("openmoji-version"),i=100,d=0,l="",I=t=>new Date(t+16510752e5).toLocaleString(),k=()=>c==null?void 0:c.getAttribute("type"),w=({emoji:t})=>{let e=[...t],n=(e.length==2&&e[1]==="️"?[e[0]]:e).map(s=>s.codePointAt(0).toString(16).padStart(4,"0")).join("-").toUpperCase(),g="/static/openmoji/svg/".concat(n,".svg");return o("img",{src:h?"".concat(g,"?v=").concat(h):g,alt:t,className:"emoji"})},p=({emoji:t})=>k()==="img"?o(w,{emoji:t}):t,T=t=>o("div",{tooltip:I(t.timestamp),children:[...t.author.map(e=>o(p,{emoji:e})),": ",...t.content.map(e=>o(p,{emoji:e}))]}),y=t=>{f.append(o(T,S({},t)))},$=t=>{let e="current-user";a(e).replaceWith(o("div",{className:k()?"openmoji":"",id:e,children:t.map(n=>o(p,{emoji:n}))}))},E=()=>{l&&!r.value&&(r.value=l,l="")},W={connecting:"Versuche mit WebSocket zu verbinden",connected:"Mit WebSocket verbunden!",disconnected:"Verbindung getrennt. Drücke hier um erneut zu versuchen."},m=t=>{let e="connection-state",n=t=="disconnected"?()=>{d=0,i=500,a(e).removeEventListener("click",n),u()}:void 0;a(e).replaceWith(o("div",{tooltip:W[t],"tooltip-position":"right",onclick:n,"data-state":t,id:e}))},N=t=>{let e=JSON.parse(t.data);switch(e.type){case"messages":{f.innerText="";for(let n of e.messages)y(n);break}case"message":{y(e.message);break}case"init":{$(e.current_user),e.current_user.join(""),m("connected"),i=100,d=0;break}case"users":{e.users;break}case"ratelimit":{E(),alert("Retry after ".concat(e.retry_after," seconds."));break}case"error":{E(),alert(e.error);break}default:console.error("Invalid type ".concat(e.type))}},u=()=>{let t=new AbortController,e={signal:t.signal};m("connecting");let n=new WebSocket((location.protocol==="https:"?"wss:":"ws:")+"//".concat(location.host,"/websocket/emoji-chat")),g=setInterval(()=>{n.readyState==n.OPEN&&n.send("")},1e4);n.addEventListener("close",s=>{if(t.abort(),clearInterval(g),s.wasClean){"Connection closed cleanly, code=".concat(s.code," reason=").concat(s.reason),m("disconnected");return}if("Connection closed, reconnecting in ".concat(i,"ms  (").concat(d,")"),m("connecting"),d>10){m("disconnected");return}setTimeout(()=>{i=Math.max(500,Math.floor(Math.min(15e3,1.5*i-200))),d++,u()},i)},e),n.addEventListener("open",s=>{m("connected")},e),n.addEventListener("error",s=>{console.error({msg:"got error from websocket",event:s})},e),n.addEventListener("message",s=>{N(s)},e),L.addEventListener("submit",s=>{r.value!==""&&(l=r.value,n.send(JSON.stringify({type:"message",message:r.value})),r.value=""),s.preventDefault()},e)};u();
// @license-end
//# sourceMappingURL=chat.js.map
