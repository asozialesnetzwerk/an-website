import{PopStateHandlers as b,setURLParam as I}from"/static/js/utils/utils.js?v=f524b6c3959bfa42";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
var s="bigint";try{BigInt(69)}catch(t){BigInt=Number,s="number"}var E=document.getElementById("output"),i=[document.getElementById("euro"),document.getElementById("mark"),document.getElementById("ost"),document.getElementById("schwarz")],c=[BigInt(1),BigInt(2),BigInt(4),BigInt(20)],y=/^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/,a=t=>/^0*$/.test(t);function m(t){if(typeof t=="string"&&(t=g(t)),typeof t!==s)return alert("Ungültiger Wert ".concat(t," mit type ").concat(typeof t)),null;typeof t=="number"&&(t=Math.floor(t));let n=t.toString();if(s==="number"&&n.includes("e")){let[l,u]=n.split("e");if(u.startsWith("-"))return"0";let[o,r]=l.split(".");r=r!=null?r:"",n=(o!=null?o:"")+r+"0".repeat(parseInt(u)-r.length)}if(a(n))return"0";let e=n.slice(-2);return(n.slice(0,-2)||"0")+(a(e)?"":","+(e.length===1?"0":"")+e)}function g(t){if(a(t))return BigInt(0);let[n,e]=[t,"00"];return t.includes(",")?[n,e]=t.split(","):t.includes(".")&&([n,e]=t.split(".")),e.length!==2&&(e=(e+"00").slice(0,2)),BigInt(n+e)}b.currencyConverter=t=>{d(g(t.state.euro.toString()))};var f=(t,n)=>I("euro",t,{euro:t},"currencyConverter",n);function d(t,n=null){var e;f((e=m(t))!=null?e:"null",!1);for(let l=0;l<4;l++){let u=m(t*c[l]);i[l].placeholder=u!=null?u:"null",l!==n&&(i[l].value=u!=null?u:"null")}}var p=()=>{E.value=i[0].value+" Euro, das sind ja "+i[1].value+" Mark; "+i[2].value+" Ostmark und "+i[3].value+" Ostmark auf dem Schwarzmarkt!"};function B(t){var n;t.preventDefault();for(let e of i)e.value=(n=m(e.value))!=null?n:"null";f(i[0].value,!0),p()}for(let t=0;t<4;t++)i[t].oninput=()=>{for(let n of i)n.className="";if(!y.test(i[t].value)){i[t].className="invalid";return}d(g(i[t].value)/c[t],t),p()};for(let t of i)t.value=t.placeholder;document.getElementById("form").onsubmit=B;
// @license-end
//# sourceMappingURL=converter.js.map
