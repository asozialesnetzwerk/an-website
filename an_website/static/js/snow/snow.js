"use strict";// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
const snow=document.getElementById("snow"),snowflakesCount=200;function showSnow(n){n?snow.style.display="block":snow.style.display="none"}function spawnSnow(n=200){for(let o=1;o<=n;o++){const t=document.createElement("p");snow.appendChild(t)}}function addCss(n){const o=document.createElement("style");o.appendChild(document.createTextNode(n)),document.getElementsByTagName("head")[0].appendChild(o)}function randomInt(n=100){return Math.floor(Math.random()*n)+1}function randomIntRange(n,o){return n=Math.ceil(n),o=Math.floor(o),Math.floor(Math.random()*(o-n+1))+n}function getRandomArbitrary(n,o){return Math.random()*(o-n)+n}function spawnSnowCSS(n=200){let o="";for(let t=1;t<=n;t++){const e=Math.random()*100,r=Math.random()*10,l=e+r,d=e+r/2,s=getRandomArbitrary(.3,.8),c=s*100,a=Math.random(),m=randomIntRange(10,30),i=randomInt(30)*-1,f=Math.random();o+=`
      #snow p:nth-child(${t}) {
        opacity: ${f};
        transform: translate(${e}vw, -10px) scale(${a});
        animation: fall-${t} ${m}s ${i}s linear infinite;
      }
      @keyframes fall-${t} {
        ${s*100}% {
          transform: translate(${l}vw, ${c}vh) scale(${a});
        }
        to {
          transform: translate(${d}vw, 100vh) scale(${a});
        }
      }
    `}addCss(o)}function createSnow(){spawnSnowCSS(snowflakesCount),snow.firstElementChild||spawnSnow(snowflakesCount)}window.onload=createSnow;// @license-end
//# sourceMappingURL=snow.js.map
