// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
var d=(e,n,t,o=!0)=>{if(typeof e=="function")return e(n);let s=document.createElement(e);return Object.entries(n).forEach(([i,r])=>{i==="children"?r==null||r.forEach(c=>{s.append(c)}):i==="className"?s.className=r:i.startsWith("on")?r&&s.addEventListener(i.slice(2),r):s.setAttribute(i,r)}),s},l=(e,n,t)=>d(e,n,t,!1),a=e=>{var t;let n=document.createDocumentFragment();return(t=e.children)==null||t.forEach(o=>{n.append(o)}),n};export{a as Fragment,d as jsx,l as jsxs};
// @license-end
//# sourceMappingURL=jsx-runtime.js.map
