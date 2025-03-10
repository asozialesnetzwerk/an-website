// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
var d=(e,t,i,o=!0)=>{if(typeof e=="function")return e(t);let s=document.createElement(e);return Object.entries(t).forEach(([r,n])=>{r==="children"?n==null||n.forEach(c=>{s.append(c)}):r==="className"?s.className=n:r.startsWith("on")?n&&s.addEventListener(r.slice(2),n):s.setAttribute(r,n)}),s},l=(e,t,i)=>d(e,t,i,!1);export{d as jsx,l as jsxs};
// @license-end
//# sourceMappingURL=jsx-runtime.js.map
