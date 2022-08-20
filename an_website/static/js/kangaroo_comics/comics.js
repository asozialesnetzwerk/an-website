"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
function startLoadingComics(){const a=(i,n,e)=>new Date(i,n-1,e,6,0,0,0),o=[[a(2021,5,25),"administratives/kaenguru-comics/25/original/"],[a(2021,9,6),"administratives/kaenguru-comics/2021-09/6/original/"],[a(2021,10,4),"administratives/kaenguru-comics/2021-10/4/original"],[a(2021,10,29),"administratives/kaenguru-comics/29/original"],[a(2021,11,3),"administratives/kaenguru-comics/2021-11/03-11-21/original"],[a(2021,12,6),"administratives/kaenguru-comics/2021-12/6/original"],[a(2022,1,29),"administratives/kaenguru-comics/2022-01/29-3/original"],[a(2022,2,7),"administratives/kaenguru-comics/08-02-22/original"],[a(2022,2,12),"administratives/kaenguru-comics/12/original"],[a(2022,2,14),"administratives/kaenguru-comics/14/original"],[a(2022,3,28),"administratives/kaenguru-comics/2022-03/kaenguru-2022-03-28/original"],[a(2022,4,4),"administratives/kaenguru-comics/2022-04/4/original"],[a(2022,5,9),"administratives/kaenguru-comics/2022-05/9/original"],[a(2022,8,15),"administratives/kaenguru-comics/2022-08/kaenguru-comics-2022-08-15/original"]],l=(i,n,e,t)=>i.getFullYear()===n&&i.getMonth()===e-1&&i.getDate()===t,M=(i,n)=>l(i,n.getFullYear(),n.getMonth()+1,n.getDate()),k=i=>i&&i.getDay()===0&&!l(i,2020,12,20),y=i=>a(i.getFullYear(),i.getMonth()+1,i.getDate()),L=()=>y(new Date),u=[],T=`/static/img/2020-11-03.jpg
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
`;function E(){const i=L(),n=y(A);for(;n.getTime()<=i.getTime();)u.push(w(n)),c(n,1)}const F=["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"],S=i=>F[i.getDay()],N=["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],x=i=>N[i.getMonth()],v=i=>"Comic von "+S(i)+", dem "+i.getDate()+". "+x(i)+" "+i.getFullYear();function p(){for(const i of d.getElementsByClassName("popup-container"))i.remove()}const C=elById("current-comic-header"),h=elById("current-img");h.onmouseover=p;function D(i){let n=w(i);n=n.startsWith("/")?n:"https://img.zeit.de/"+n,h.src=n,C.innerText="Neuster "+v(i)+":",C.href=n}const z=a(2020,12,3),Y=/administratives\/kaenguru-comics\/kaenguru-(\d{2,3})(?:-2)?\/original\/?/,A=a(2021,1,19),W=/administratives\/kaenguru-comics\/(\d{4})-(\d{2})\/(\d{2})\/original\/?/,J=/\/static\/img\/(\d{4})-(\d{1,2})-(\d{1,2})\.jpg/;function O(i){for(const e of[W,J]){const t=i.toLowerCase().match(e);if(t&&t.length>3)return a(t[1],t[2],t[3])}const n=i.toLowerCase().match(Y);if(n&&n.length>1){const e=n[1]-5,t=new Date(z.getTime());for(let r=0;r<e;r++)t.setTime(c(t,k(t)?2:1));return k(t)?c(t,1):t}switch(i=i.toLowerCase().trim(),i){case"administratives/kaenguru-comics/pilot-kaenguru/original":return a(2020,11,29);case"administratives/kaenguru-comics/pow-kaenguru/original":return a(2020,11,30);case"static/img/kaenguru-announcement/original":return a(2020,11,30);case"administratives/kaenguru-comics/der-baum-kaenguru/original":return a(2020,12,1);case"administratives/kaenguru-comics/warnung-kaenguru/original":return a(2020,12,2);case"administratives/2020-12/kaenguru-comics-kaenguru-019/original":return a(2020,12,19)}for(const e of o)if(i===e[1])return e[0]}const R="administratives/kaenguru-comics/%y-%m/%d/original";function w(i){for(const t of o)if(M(i,t[0]))return t[1];const n=(i.getMonth()+1).toString(),e=i.getDate().toString();return R.replace("%y",i.getFullYear().toString()).replace("%m",n.length===2?n:"0"+n).replace("%d",e.length===2?e:"0"+e)}function c(i,n){return i.setTime(i.getTime()+n*1e3*60*60*24),i.setHours(6),i}const b=7,B=elById("load-button"),I=elById("old-comics-list");let g=0;function j(){for(let i=0;i<b;i++){g++;const n=u.length-g;if(n<0)break;let e=u[n];const t=O(e);e=e.startsWith("/")?e:"https://img.zeit.de/"+e;const r=d.createElement("li"),m=d.createElement("a");m.classList.add("comic-header"),m.innerText=v(t)+":",m.href=e,m.style.fontSize="25px",r.appendChild(m),r.appendChild(d.createElement("br"));const s=d.createElement("img");s.classList.add("normal-img"),s.src=e,s.alt=v(t),s.onclick=()=>q(s),s.onerror=()=>{k(t)?I.removeChild(r):r.append(" konnte nicht geladen werden.")},r.appendChild(s),I.appendChild(r)}g>=u.length&&(B.style.opacity="0",B.style.visibility="invisible")}elById("load-button").onclick=j;function q(i){p();const n=d.createElement("div");n.classList.add("popup-container"),n.onmouseleave=()=>n.remove(),n.onclick=()=>p();const e=i.cloneNode(!0);e.classList.remove("normal-img"),e.classList.add("popup-img");const t=d.createElement("img");t.classList.add("close-button"),t.src="/static/img/close.svg?v=0",n.appendChild(e),n.appendChild(t),i.parentNode.appendChild(n)}u.concat(T.split(`
`)),E();const f=c(L(),1);D(f),h.onerror=i=>{c(f,-1),D(f),g<b&&g++}}(()=>{const a=elById("start-button-no_3rd_party");if(a){let l=function(){a.remove(),o.classList.remove("hidden"),startLoadingComics()};const o=elById("comic-content-container");a.onclick=l,o.classList.add("hidden")}else startLoadingComics()})();// @license-end
//# sourceMappingURL=comics.js.map
