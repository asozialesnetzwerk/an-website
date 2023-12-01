"use strict";// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
const snow=document.getElementById("snow"),snowflakesCount=200;function showSnow(n){n?snow.style.display="block":snow.style.display="none"}function addCss(n){const o=document.createElement("style");o.appendChild(document.createTextNode(n)),document.getElementsByTagName("head")[0].appendChild(o)}function randomInt(n=100){return Math.floor(Math.random()*n)+1}function randomIntRange(n,o){return n=Math.ceil(n),o=Math.floor(o),Math.floor(Math.random()*(o-n+1))+n}function getRandomArbitrary(n,o){return Math.random()*(o-n)+n}function spawnSnowCSS(n=200){let o="";for(let t=1;t<=n;t++){const a=Math.random()*100,r=Math.random()*10,d=a+r,l=a+r/2,s=getRandomArbitrary(.3,.8),c=s*100,e=Math.random(),m=randomIntRange(10,30),i=randomInt(30)*-1,u=Math.random();o+=`
      #snow p:nth-child(${t}) {
        opacity: ${u};
        transform: translate(${a}vw, -10px) scale(${e});
        animation: fall-${t} ${m}s ${i}s linear infinite;
      }
      @keyframes fall-${t} {
        ${s*100}% {
          transform: translate(${d}vw, ${c}vh) scale(${e});
        }
        to {
          transform: translate(${l}vw, 100vh) scale(${e});
        }
      }
    `}addCss(o)}function createSnow(){spawnSnowCSS(snowflakesCount)}window.onload=createSnow;// @license-end
//# sourceMappingURL=snow.js.map
