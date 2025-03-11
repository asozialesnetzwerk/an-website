var M=Object.defineProperty;var v=Object.getOwnPropertySymbols;var j=Object.prototype.hasOwnProperty,L=Object.prototype.propertyIsEnumerable;var b=(t,e,n)=>e in t?M(t,e,{enumerable:!0,configurable:!0,writable:!0,value:n}):t[e]=n,S=(t,e)=>{for(var n in e||(e={}))j.call(e,n)&&b(t,n,e[n]);if(v)for(var n of v(e))L.call(e,n)&&b(t,n,e[n]);return t};import{Fragment as C,jsx as o,jsxs as A}from"/static/js/utils/jsx-runtime.js?v=07bb745a37bfede0";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import{e as a}from"/static/js/utils/utils.js?v=b4ed019200cc7b4b";var r=a("message-input"),I=r.form,f=a("message-section"),c=a("openmoji-attribution"),h=c==null?void 0:c.getAttribute("openmoji-version"),i=100,d=0,l="",w=t=>new Date(t+16510752e5).toLocaleString(),k=()=>c==null?void 0:c.getAttribute("type"),T=({emoji:t})=>{let e=[...t],n=(e.length==2&&e[1]==="️"?[e[0]]:e).map(s=>s.codePointAt(0).toString(16).padStart(4,"0")).join("-").toUpperCase(),g="/static/openmoji/svg/".concat(n,".svg");return o("img",{src:h?"".concat(g,"?v=").concat(h):g,alt:t,className:"emoji"})},p=({emoji:t})=>k()==="img"?o(T,{emoji:t}):t,$=t=>A("div",{tooltip:w(t.timestamp),children:[o(C,{children:t.author.map(e=>o(p,{emoji:e}))}),": ",o(C,{children:t.content.map(e=>o(p,{emoji:e}))})]}),y=t=>{f.append(o($,S({},t)))},W=t=>{let e="current-user";a(e).replaceWith(o("div",{className:k()?"openmoji":"",id:e,children:t.map(n=>o(p,{emoji:n}))}))},E=()=>{l&&!r.value&&(r.value=l,l="")},N={connecting:"Versuche mit WebSocket zu verbinden",connected:"Mit WebSocket verbunden!",disconnected:"Verbindung getrennt. Drücke hier um erneut zu versuchen."},m=t=>{let e="connection-state",n=t=="disconnected"?()=>{d=0,i=500,a(e).removeEventListener("click",n),u()}:void 0;a(e).replaceWith(o("div",{tooltip:N[t],"tooltip-position":"right",onclick:n,"data-state":t,id:e}))},_=t=>{let e=JSON.parse(t.data);switch(e.type){case"messages":{f.innerText="";for(let n of e.messages)y(n);break}case"message":{y(e.message);break}case"init":{W(e.current_user),e.current_user.join(""),m("connected"),i=100,d=0;break}case"users":{e.users;break}case"ratelimit":{E(),alert("Retry after ".concat(e.retry_after," seconds."));break}case"error":{E(),alert(e.error);break}default:console.error("Invalid type ".concat(e.type))}},u=()=>{let t=new AbortController,e={signal:t.signal};m("connecting");let n=new WebSocket((location.protocol==="https:"?"wss:":"ws:")+"//".concat(location.host,"/websocket/emoji-chat")),g=setInterval(()=>{n.readyState==n.OPEN&&n.send("")},1e4);n.addEventListener("close",s=>{if(t.abort(),clearInterval(g),s.wasClean){"Connection closed cleanly, code=".concat(s.code," reason=").concat(s.reason),m("disconnected");return}if("Connection closed, reconnecting in ".concat(i,"ms  (").concat(d,")"),m("connecting"),d>10){m("disconnected");return}setTimeout(()=>{i=Math.max(500,Math.floor(Math.min(15e3,1.5*i-200))),d++,u()},i)},e),n.addEventListener("open",s=>{m("connected")},e),n.addEventListener("error",s=>{console.error({msg:"got error from websocket",event:s})},e),n.addEventListener("message",s=>{_(s)},e),I.addEventListener("submit",s=>{r.value!==""&&(l=r.value,n.send(JSON.stringify({type:"message",message:r.value})),r.value=""),s.preventDefault()},e)};u();
// @license-end
//# sourceMappingURL=chat.js.map
