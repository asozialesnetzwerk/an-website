// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
window.lastLocation=window.location;function post(url,params={},ondata=(data)=>console.log(data),onerror=(data)=>console.error(data)){fetch(url,{method:"POST",body:JSON.stringify(params),headers:{"Accept":"application/json"}}).then(response=>response.json()).catch(onerror).then(ondata).catch(onerror);}
function get(url,params={},ondata=(data)=>console.log(data),onerror=(data)=>console.error(data)){fetch(url+(!params?"":"?"+(new URLSearchParams(params)).toString()),{method:"GET",headers:{"Accept":"application/json"}}).then(response=>response.json()).catch(onerror).then(ondata).catch(onerror);}
window.PopStateHandlers={"replaceURL":(state)=>{window.lastLocation===state["origin"]||window.location.reload();},"URLParamChange":(state)=>{window.location.reload();}};function setURLParam(param,value,state,stateType="URLParamChange",push=true){const urlParams=new URLSearchParams(window.location.search);urlParams.set(param,value);const newUrl=`${window.location.origin}${window.location.pathname}?${urlParams.toString()}`;state["stateType"]=stateType;if(push){history.pushState(state,newUrl,newUrl);}else{history.replaceState(state,newUrl,newUrl)}
return newUrl;}
window.onpopstate=(event)=>{if(event.state&&event.state["stateType"]&&window.PopStateHandlers[event.state["stateType"]]){window.PopStateHandlers[event.state["stateType"]](event);window.lastLocation=window.location;}else{console.error("Couldn't handle state. ",event.state);window.location.reload();}}
function fixHref(href){if(window.dynLoadGetFixedHref){return window.dynLoadGetFixedHref(href);}
return href;}
// @license-end
