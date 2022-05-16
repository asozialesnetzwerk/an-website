// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
function showSitePane(){elById("site-pane").style.right="0";}
function hideSitePane(){elById("site-pane").style.right="-70%";}
(()=>{const openPane=elById("open-pane");const sitePane=elById("site-pane");const belongsToSitePane=(el)=>(el===openPane||el===sitePane||sitePane.contains(el));openPane.onmouseover=showSitePane;sitePane.onmouseleave=hideSitePane;sitePane.onfocusin=showSitePane;sitePane.onfocusout=hideSitePane;openPane.onclick=showSitePane;d.onclick=(e)=>belongsToSitePane(e.target)||hideSitePane();const startPos={x:null,y:null};d.ontouchstart=(e)=>{startPos.x=e.touches[0].clientX;startPos.y=e.touches[0].clientY;};d.ontouchmove=(e)=>{if(startPos.x===null||startPos.y===null)return;const diffX=startPos.x-e.touches[0].clientX;const diffY=startPos.y-e.touches[0].clientY;startPos.x=null;startPos.y=null;if(diffX===0&&diffY===0)return;if(Math.abs(diffX)>Math.abs(diffY)){if(diffX>0){showSitePane();}else{hideSitePane();}
e.preventDefault();}};})()
// @license-end
