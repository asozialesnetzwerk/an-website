"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
function startLoadingComics(){const e=(i,n,a)=>new Date(i,n-1,a,6,0,0,0),o=[[e(2021,5,25),"administratives/kaenguru-comics/25/original/"],[e(2021,9,6),"administratives/kaenguru-comics/2021-09/6/original/"],[e(2021,10,4),"administratives/kaenguru-comics/2021-10/4/original"],[e(2021,10,29),"administratives/kaenguru-comics/29/original"],[e(2021,11,3),"administratives/kaenguru-comics/2021-11/03-11-21/original"],[e(2021,12,6),"administratives/kaenguru-comics/2021-12/6/original"],[e(2022,1,29),"administratives/kaenguru-comics/2022-01/29-3/original"],[e(2022,2,7),"administratives/kaenguru-comics/08-02-22/original"],[e(2022,2,12),"administratives/kaenguru-comics/12/original"],[e(2022,2,14),"administratives/kaenguru-comics/14/original"],[e(2022,3,28),"administratives/kaenguru-comics/2022-03/kaenguru-2022-03-28/original"],[e(2022,4,4),"administratives/kaenguru-comics/2022-04/4/original"],[e(2022,5,9),"administratives/kaenguru-comics/2022-05/9/original"],[e(2022,8,15),"administratives/kaenguru-comics/2022-08/kaenguru-comics-2022-08-15/original"],[e(2022,8,29),"administratives/kaenguru-comics/2022-08/29-3/original"]],h=(i,n,a,t)=>i.getFullYear()===n&&i.getMonth()===a-1&&i.getDate()===t,I=(i,n)=>h(i,n.getFullYear(),n.getMonth()+1,n.getDate()),l=i=>i&&i.getDay()===0&&!h(i,2020,12,20),D=i=>e(i.getFullYear(),i.getMonth()+1,i.getDate()),f=()=>D(new Date),u=[],w=`/static/img/2020-11-03.jpg
administratives/kaenguru-comics/pilot-kaenguru/original
administratives/kaenguru-comics/pow-kaenguru/original
static/img/kaenguru-announcement/original
administratives/kaenguru-comics/der-baum-kaenguru/original
administratives/kaenguru-comics/warnung-kaenguru/original
administratives/kaenguru-comics/kaenguru-005/original
administratives/kaenguru-comics/kaenguru-006/original
administratives/kaenguru-comics/kaenguru-007/original
administratives/kaenguru-comics/kaenguru-008/original
administratives/kaenguru-comics/kaenguru-009/original
administratives/kaenguru-comics/kaenguru-010/original
administratives/kaenguru-comics/kaenguru-011/original
administratives/kaenguru-comics/kaenguru-012/original
administratives/kaenguru-comics/kaenguru-013/original
administratives/kaenguru-comics/kaenguru-014/original
administratives/kaenguru-comics/kaenguru-015/original
administratives/kaenguru-comics/kaenguru-016/original
administratives/kaenguru-comics/kaenguru-017/original
administratives/kaenguru-comics/kaenguru-018/original
administratives/2020-12/kaenguru-comics-kaenguru-019/original
administratives/kaenguru-comics/kaenguru-020/original
administratives/kaenguru-comics/kaenguru-021/original
administratives/kaenguru-comics/kaenguru-023/original
administratives/kaenguru-comics/kaenguru-024/original
administratives/kaenguru-comics/kaenguru-025/original
administratives/kaenguru-comics/kaenguru-026/original
administratives/kaenguru-comics/kaenguru-027/original
administratives/kaenguru-comics/kaenguru-028/original
administratives/kaenguru-comics/kaenguru-029/original
administratives/kaenguru-comics/kaenguru-030/original
administratives/kaenguru-comics/kaenguru-031/original
administratives/kaenguru-comics/kaenguru-032/original
administratives/kaenguru-comics/kaenguru-033/original
administratives/kaenguru-comics/kaenguru-034/original
administratives/kaenguru-comics/kaenguru-035/original
administratives/kaenguru-comics/kaenguru-036/original
administratives/kaenguru-comics/kaenguru-037/original
administratives/kaenguru-comics/kaenguru-038-2/original
administratives/kaenguru-comics/kaenguru-039/original
administratives/kaenguru-comics/kaenguru-040/original
administratives/kaenguru-comics/kaenguru-41/original
administratives/kaenguru-comics/kaenguru-42/original
administratives/kaenguru-comics/kaenguru-43/original
administratives/kaenguru-comics/kaenguru-44/original
administratives/kaenguru-comics/kaenguru-045/original
`;function E(){const i=f(),n=D(z);for(;n.getTime()<=i.getTime();)u.push(b(n)),g(n,1)}const B=["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"],H=i=>B[i.getDay()],F=["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],N=i=>F[i.getMonth()],d=i=>`Comic von ${H(i)}, dem ${i.getDate()}. ${N(i)} ${i.getFullYear()}`;function k(){for(const i of document.getElementsByClassName("popup-container"))i.remove()}const L=elById("current-comic-header"),v=elById("current-img");v.onmouseover=k;function y(i){let n=b(i);n=n.startsWith("/")?n:"https://img.zeit.de/"+n,v.src=n,L.innerText="Neuster "+d(i)+":",L.href=n}const S=e(2020,12,3),x=/administratives\/kaenguru-comics\/kaenguru-(\d{2,3})(?:-2)?\/original\/?/,z=e(2021,1,19),Y=/administratives\/kaenguru-comics\/(\d{4})-(\d{2})\/(\d{2})\/original\/?/,A=/\/static\/img\/(\d{4})-(\d{1,2})-(\d{1,2})\.jpg/;function W(i){for(const a of[Y,A]){const t=i.toLowerCase().match(a);if(t&&t.length>3)return e(parseInt(t[1]),parseInt(t[2]),parseInt(t[3]))}const n=i.toLowerCase().match(x);if(n&&n.length>1){const a=parseInt(n[1])-5,t=new Date(S.getTime());for(let r=0;r<a;r++)t.setTime(g(t,l(t)?2:1).getTime());return l(t)?g(t,1):t}switch(i=i.toLowerCase().trim(),i){case"administratives/kaenguru-comics/pilot-kaenguru/original":return e(2020,11,29);case"administratives/kaenguru-comics/pow-kaenguru/original":return e(2020,11,30);case"static/img/kaenguru-announcement/original":return e(2020,11,30);case"administratives/kaenguru-comics/der-baum-kaenguru/original":return e(2020,12,1);case"administratives/kaenguru-comics/warnung-kaenguru/original":return e(2020,12,2);case"administratives/2020-12/kaenguru-comics-kaenguru-019/original":return e(2020,12,19)}for(const a of o)if(i===a[1])return a[0];return null}const $="administratives/kaenguru-comics/%y-%m/%d/original";function b(i){for(const t of o)if(I(i,t[0]))return t[1];const n=(i.getMonth()+1).toString(),a=i.getDate().toString();return $.replace("%y",i.getFullYear().toString()).replace("%m",n.length===2?n:"0"+n).replace("%d",a.length===2?a:"0"+a)}function g(i,n){return i.setTime(i.getTime()+n*1e3*60*60*24),i.setHours(6),i}const C=7,T=elById("load-button"),M=elById("old-comics-list");let c=0;const J=()=>{for(let i=0;i<C;i++){c++;const n=u.length-c;if(n<0)break;let a=u[n];const t=W(a);if(t===null){console.error("No date found for "+a);continue}a=a.startsWith("/")?a:"https://img.zeit.de/"+a;const r=document.createElement("li"),m=document.createElement("a");m.classList.add("comic-header"),m.innerText=d(t)+":",m.href=a,m.style.fontSize="25px",r.appendChild(m),r.appendChild(document.createElement("br"));const s=document.createElement("img");s.classList.add("normal-img"),s.src=a,s.alt=d(t),s.onclick=()=>O(s),s.onerror=()=>{l(t)?M.removeChild(r):r.append(" konnte nicht geladen werden.")},r.appendChild(s),M.appendChild(r)}c>=u.length&&(T.style.opacity="0",T.style.visibility="invisible")};elById("load-button").onclick=J;const O=i=>{k();const n=document.createElement("div");n.classList.add("popup-container"),n.onmouseleave=()=>n.remove(),n.onclick=()=>k();const a=i.cloneNode(!0);a.classList.remove("normal-img"),a.classList.add("popup-img");const t=document.createElement("img");t.classList.add("close-button"),t.src="/static/img/close.svg?v=0",n.appendChild(a),n.appendChild(t),i.parentNode.appendChild(n)};u.concat(w.split(`
`)),E();const p=g(f(),1);y(p),v.onerror=()=>{g(p,-1),y(p),c<C&&c++}}(()=>{const e=elById("start-button-no_3rd_party");if(e!==null){const o=elById("comic-content-container");e.onclick=()=>{e.remove(),o.classList.remove("hidden"),startLoadingComics()},o.classList.add("hidden")}else startLoadingComics()})();// @license-end
//# sourceMappingURL=comics.js.map
