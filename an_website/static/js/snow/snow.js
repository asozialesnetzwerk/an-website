"use strict";const snow=document.getElementById("snow");let snowflakesCount=200,bodyHeightPx=null,pageHeightVh=null;function setHeightVariables(){bodyHeightPx=document.documentElement.getBoundingClientRect().height,pageHeightVh=100*Math.max(bodyHeightPx/window.innerHeight,1)}function getSnowAttributes(){snow&&(snowflakesCount=Number(snow.attributes?.count?.value||snowflakesCount))}function showSnow(n){n?snow.style.display="block":snow.style.display="none"}function spawnSnow(n=200){for(let t=1;t<=n;t++){const o=document.createElement("p");snow.appendChild(o)}}function addCss(n){const t=document.createElement("style");t.appendChild(document.createTextNode(n)),document.getElementsByTagName("head")[0].appendChild(t)}function randomInt(n=100){return Math.floor(Math.random()*n)+1}function randomIntRange(n,t){return n=Math.ceil(n),t=Math.floor(t),Math.floor(Math.random()*(t-n+1))+n}function getRandomArbitrary(n,t){return Math.random()*(t-n)+n}function spawnSnowCSS(n=200){let t="";for(let o=1;o<=n;o++){const e=Math.random()*100,l=Math.random()*10,s=e+l,c=e+l/2,r=getRandomArbitrary(.3,.8),d=r*100,a=Math.random(),i=randomIntRange(10,30),m=randomInt(30)*-1,f=Math.random();t+=`
      #snow p:nth-child(${o}) {
        opacity: ${f};
        transform: translate(${e}vw, -10px) scale(${a});
        animation: fall-${o} ${i}s ${m}s linear infinite;
      }
      @keyframes fall-${o} {
        ${r*100}% {
          transform: translate(${s}vw, ${d}vh) scale(${a});
        }
        to {
          transform: translate(${c}vw, 100vh) scale(${a});
        }
      }
    `}addCss(t)}function createSnow(){setHeightVariables(),getSnowAttributes(),spawnSnowCSS(snowflakesCount),snow.firstElementChild||spawnSnow(snowflakesCount)}window.onload=createSnow;
//# sourceMappingURL=snow.js.map
