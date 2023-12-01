"use strict";// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
const snow=document.getElementById("snow");let snowflakesCount=200,bodyHeightPx,pageHeightVh;function setHeightVariables(){bodyHeightPx=document.documentElement.getBoundingClientRect().height,pageHeightVh=100*Math.max(bodyHeightPx/window.innerHeight,1)}function getSnowAttributes(){snow&&(snowflakesCount=Number(snow.attributes?.count?.value||snowflakesCount))}function showSnow(n){n?snow.style.display="block":snow.style.display="none"}function spawnSnow(n=200){for(let t=1;t<=n;t++){const e=document.createElement("p");snow.appendChild(e)}}function addCss(n){const t=document.createElement("style");t.appendChild(document.createTextNode(n)),document.getElementsByTagName("head")[0].appendChild(t)}function randomInt(n=100){return Math.floor(Math.random()*n)+1}function randomIntRange(n,t){return n=Math.ceil(n),t=Math.floor(t),Math.floor(Math.random()*(t-n+1))+n}function getRandomArbitrary(n,t){return Math.random()*(t-n)+n}function spawnSnowCSS(n=200){let t="";for(let e=1;e<=n;e++){const o=Math.random()*100,r=Math.random()*10,d=o+r,i=o+r/2,l=getRandomArbitrary(.3,.8),s=l*100,a=Math.random(),c=randomIntRange(10,30),m=randomInt(30)*-1,u=Math.random();t+=`
      #snow p:nth-child(${e}) {
        opacity: ${u};
        transform: translate(${o}vw, -10px) scale(${a});
        animation: fall-${e} ${c}s ${m}s linear infinite;
      }
      @keyframes fall-${e} {
        ${l*100}% {
          transform: translate(${d}vw, ${s}vh) scale(${a});
        }
        to {
          transform: translate(${i}vw, 100vh) scale(${a});
        }
      }
    `}addCss(t)}function createSnow(){setHeightVariables(),getSnowAttributes(),spawnSnowCSS(snowflakesCount),snow.firstElementChild||spawnSnow(snowflakesCount)}window.onload=createSnow;// @license-end
//# sourceMappingURL=snow.js.map
