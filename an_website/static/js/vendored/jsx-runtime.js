var d=Object.defineProperty;var o=Object.getOwnPropertySymbols;var p=Object.prototype.hasOwnProperty,u=Object.prototype.propertyIsEnumerable;var l=(n,e,t)=>e in n?d(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t,c=(n,e)=>{for(var t in e||(e={}))p.call(e,t)&&l(n,t,e[t]);if(o)for(var t of o(e))u.call(e,t)&&l(n,t,e[t]);return n};// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
var a=(n,e,...t)=>{if(typeof n=="function")return n(c({},e),t);let r=document.createElement(n);e&&Object.entries(e).forEach(([s,i])=>{if(s==="className"){r.classList.add(...(i||"").trim().split(" "));return}r.setAttribute(s,i)});for(let s of t)r.append(s);return r};export{a as jsx,a as jsxs};
// @license-end
//# sourceMappingURL=jsx-runtime.js.map
