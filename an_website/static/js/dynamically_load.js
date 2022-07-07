// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
const bodyDiv=elById("body");const lastLoaded=[];function dynLoadOnData(data,onpopstate){if(!data){error("No data received");return;}
if(data["redirect"]){w.location.href=data["redirect"];return;}
const url=data["url"];if(!url){error("No URL in data ",data);return;}
log("Handling data",data);if(!onpopstate){if(lastLoaded.length===1&&lastLoaded[0]===url){log("Data url is the same as last loaded, ignoring");return;}
history.pushState({"data":data,"url":url,"stateType":"dynLoad"},data["title"],url);w.lastLocation=url;}
if(!data["body"]){w.location.reload();return;}
d.onkeydown=()=>{};bodyDiv.innerHTML=data["body"];if(data["css"]){const style=d.createElement("style");style.innerHTML=data["css"];bodyDiv.appendChild(style);}
if(data["stylesheets"]){for(const scriptURL of data["stylesheets"]){const link=d.createElement("link");link.rel="stylesheet";link.type="text/css";link.href=scriptURL;bodyDiv.appendChild(link);}}
if(data["scripts"]){for(const script of data["scripts"]){if(script["src"]){const scriptElement=d.createElement("script");scriptElement.src=script["src"];bodyDiv.appendChild(scriptElement);}else{error("Script without src",script);}}}
if(w.hideSitePane)hideSitePane();d.title=data["title"];const titleElement=elById("title");titleElement.setAttribute("short_title",data["short_title"]||data["title"]);titleElement.innerText=data["title"];dynLoadReplaceAnchors();w.urlData=data;return true;}
function dynLoadReplaceAnchors(){for(const anchor of d.getElementsByTagName("A"))
dynLoadReplaceHrefOnAnchor(anchor);}
function dynLoadReplaceHrefOnAnchor(anchor){if(anchor.hasAttribute("no-dynload"))
return;dynLoadFixHref(anchor);}
function dynLoadFixHref(anchor){if(anchor.target==="_blank")return;const href=(anchor.href.startsWith("/")?(w.location.origin+anchor.href):anchor.href).trim();const hrefWithoutQuery=href.split("?")[0];if(!href.startsWith(w.location.origin)||(hrefWithoutQuery.split("/").pop().includes(".")&&hrefWithoutQuery!==(w.location.origin+"/redirect"))||hrefWithoutQuery===(w.location.origin+"/chat"))return;if(href.startsWith("#")||href.startsWith(w.location.href.split("#")[0]+"#"))return;anchor.onclick=(e)=>{dynLoad(href);e.preventDefault();}}
function dynLoad(url){log("Loading url",url);history.replaceState({"data":w.urlData,"url":w.location.href,"scrollPos":[d.documentElement.scrollLeft||d.body.scrollLeft,d.documentElement.scrollTop||d.body.scrollTop],"stateType":"dynLoad"},d.title,w.location.href);dynLoadSwitchToURL(url);}
function dynLoadSwitchToURL(url,allowSameUrl=false){if(!allowSameUrl&&url===w.location.href){log("URL is the same as current, just hide site pane");if(w.hideSitePane)hideSitePane();return;}
bodyDiv.prepend("Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu.");get(url,"",(data)=>dynLoadOnData(data,false),(error)=>{log(error);if(url===w.location.href){w.location.reload();}else{w.location.href=url;}});}
function dynLoadOnPopState(event){if(event.state){log("Popstate",event.state);if(!(event.state["data"]&&dynLoadOnData(event.state,true))){dynLoadSwitchToURL(event.state["url"]||w.location.href,true);}
if(event.state["scrollPos"]){w.scrollTo(event.state["scrollPos"][0],event.state["scrollPos"][1]);return;}}
error("Couldn't handle state. ",event.state);w.location.reload();}
w.PopStateHandlers["dynLoad"]=dynLoadOnPopState;dynLoadReplaceAnchors();
// @license-end
