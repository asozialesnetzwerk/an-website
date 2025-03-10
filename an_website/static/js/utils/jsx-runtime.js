// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
var l=(e,n,i,o=!0)=>{if(typeof e=="function")return e(n);let t=document.createElement(e);return Object.entries(n).forEach(([r,s])=>{r==="children"?s==null||s.forEach(c=>{t.append(c)}):r==="className"?t.className=s:r.startsWith("on")?t.addEventListener(r.slice(2),s):t.setAttribute(r,s)}),t},d=(e,n,i)=>l(e,n,i,!1);export{l as jsx,d as jsxs};
// @license-end
//# sourceMappingURL=jsx-runtime.js.map
