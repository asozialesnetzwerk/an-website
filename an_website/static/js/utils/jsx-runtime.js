// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
var l=(e,n,t,o=!0)=>{if(typeof e=="function")return e(n);let i=document.createElement(e);return Object.entries(n).forEach(([s,r])=>{s==="children"?r==null||r.forEach(d=>{i.append(d)}):s==="className"?i.className=r:s.startsWith("on")?r&&i.addEventListener(s.slice(2),r):i.setAttribute(s,r)}),i},a=(e,n,t)=>l(e,n,t,!1),c=e=>{var t;let n=document.createDocumentFragment();return(t=e.children)==null||t.forEach(o=>{n.append(o)}),n};export{c as Fragment,l as jsx,a as jsxs};
// @license-end
//# sourceMappingURL=jsx-runtime.js.map
