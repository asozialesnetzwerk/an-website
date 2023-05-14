"use strict";// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
window.showSnow=(()=>{const t=Math.random,d=document.getElementById("snow"),i=200;function m(n){const o=document.createElement("style");o.appendChild(document.createTextNode(n)),document.getElementsByTagName("head")[0].appendChild(o)}function u(n=100){return Math.floor(t()*n)+1}function f(n,o){return n=Math.ceil(n),o=Math.floor(o),Math.floor(t()*(o-n+1))+n}function w(n,o){return t()*(o-n)+n}function y(n=200){const o=(e,r,a)=>`transform: translate(${e}, ${r}) scale(${a});`;let l="";for(let e=1;e<=n;e++){const r=t()*100,a=t()*10,h=r+a,$=r+a/2,c=w(.3,.8),g=c*100,s=t(),p=f(10,30),v=u(30)*-1;l+=`
#snow p:nth-child(${e}) {
  opacity: ${t()};
  ${o(r+"vw","-10px",s)}
  animation: fall-${e} ${p}s ${v}s linear infinite;
}
@keyframes fall-${e} {
  ${c*100}% {${o(h+"vw",g+"vh",s)}}
  to {${o($+"vw","100vh",s)}}
}`}m(l)}function b(){y(i)}return window.onload=b,n=>{n?d.style.display="block":d.style.display="none"}})();// @license-end
//# sourceMappingURL=snow.js.map
