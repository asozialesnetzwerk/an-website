// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(()=>{const messageInput=elById("message-input");const messageSection=elById("message-section");const usingOpenMoji=elById("open-moji-attribution");const connectionIndicator=elById("connection-state");const currentUser=elById("current-user");let reconnectTimeout=100;let reconnectTries=0;let lastMessage="";const timeStampToText=(timestamp)=>{return new Date(timestamp+1_651_075_200_000).toLocaleString();}
const appendMessage=(msg)=>{let el=document.createElement("div");if(usingOpenMoji&&usingOpenMoji.getAttribute("type")!=="font"){for(let emoji of msg.author){el.append(emojiToIMG(emoji));}
el.innerHTML+=": ";for(let emoji of msg.content)
el.append(emojiToIMG(emoji));}else{el.innerText=`${msg.author.join("")}: ${msg.content.join("")}`;}
el.setAttribute("tooltip",timeStampToText(msg.timestamp));messageSection.append(el);}
const displayCurrentUser=(name)=>{currentUser.innerHTML="";if(usingOpenMoji&&usingOpenMoji.getAttribute("type")!=="font"){for(let emoji of name){currentUser.append(emojiToIMG(emoji));}
return;}
currentUser.innerText=name.join("");}
const emojiToIMG=(emoji)=>{let emojiCode=[...emoji].map(e=>e.codePointAt(0).toString(16).padStart(4,'0')).join(`-`).toUpperCase();let imgEl=document.createElement("img");imgEl.src=`/static/img/openmoji-svg-14.0/${emojiCode}.svg`;imgEl.classList.add("emoji")
imgEl.alt=emoji;return imgEl;}
const resetLastMessage=()=>{if(lastMessage&&!messageInput.value){messageInput.value=lastMessage;lastMessage="";}}
const setConnectionState=(state)=>{let tooltip;connectionIndicator.onclick=()=>{};if(state==="connecting"){tooltip="Versuche mit Websocket zu verbinden";}else if(state==="connected"){tooltip="Mit Websocket verbunden!";}else if(state==="disconnected"){tooltip="Verbindung getrennt. Drücke hier um erneut zu versuchen.";connectionIndicator.onclick=()=>{reconnectTries=0;reconnectTimeout=500;connectionIndicator.onclick=()=>{};openWS();}}else{console.error("invalid state",state);return;}
connectionIndicator.setAttribute("state",state);connectionIndicator.setAttribute("tooltip",tooltip);}
const handleWebsocketData=(event)=>{const data=JSON.parse(event.data);switch(data["type"]){case"messages":{messageSection.innerText="";for(let msg of data["messages"]){appendMessage(msg);}
break;}
case"message":{appendMessage(data["message"]);break;}
case"init":{displayCurrentUser(data["current_user"])
console.log("Connected as",data["current_user"].join(""));setConnectionState("connected");reconnectTimeout=100;reconnectTries=0;break;}
case"users":{console.debug("Recieved users data",data["users"]);break;}
case"ratelimit":{resetLastMessage();alert(`Retry after ${data["Retry-After"]} seconds.`);break;}
case"error":{resetLastMessage();alert(data["error"]);break;}
default:{console.error(`Invalid type ${data["type"]}`);}}}
const openWS=()=>{setConnectionState("connecting");let ws=new WebSocket((w.location.protocol==="https:"?"wss:":"ws:")
+`//${w.location.host}/websocket/emoji-chat`);let pingInterval=setInterval(()=>ws.send(""),10_000);ws.onclose=(event)=>{messageInput.form.onsubmit=()=>{};if(event.wasClean){console.debug(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);setConnectionState("disconnected");return;}
console.debug(`Connection closed, reconnecting in ${reconnectTimeout}ms`);setConnectionState("connecting");clearInterval(pingInterval);if(reconnectTries>20){setConnectionState("disconnected");return;}
setTimeout(()=>{reconnectTimeout=Math.max(500,Math.floor(Math.min(15000,1.5*reconnectTimeout-200)));reconnectTries++;openWS();},reconnectTimeout)};ws.onopen=(event)=>console.debug("Opened WebSocket",event);ws.onmessage=handleWebsocketData;messageInput.form.onsubmit=(event)=>{if(messageInput.value!==""){lastMessage=messageInput.value;ws.send(JSON.stringify({"type":"message","message":messageInput.value,}));messageInput.value="";}
event.preventDefault();}}
openWS();})();
// @license-end
