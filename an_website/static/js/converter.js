// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(()=>{let bigIntType="bigint";try{BigInt(69);}catch(e){BigInt=Number;bigIntType="number";}
const output=elById("output");const fields=[elById("euro"),elById("mark"),elById("ost"),elById("schwarz")];const factors=[BigInt(1),BigInt(2),BigInt(4),BigInt(20)];const numberRegex=/^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/;const isZero=(str)=>/^0*$/.test(str);function getDisplayValue(wert){if(typeof wert==="string")
wert=strToBigInt(wert);if(typeof wert!==bigIntType)
alert(`Ungültiger Wert ${wert} mit type ${typeof wert}`);if(bigIntType==="number")wert=Math.floor(wert);let str=wert.toString();if(bigIntType==="number"&&str.includes("e")){let[num,pow]=str.split("e");if(pow.startsWith("-"))return"0";let[int,dec]=num.split(".");dec=dec||"";str=int+dec+"0".repeat(pow-dec.length);}
if(isZero(str))return"0";let dec=str.slice(-2);return((str.slice(0,-2)||"0")
+(isZero(dec)?"":","+(dec.length===1?"0":"")+dec));}
function strToBigInt(str){if(typeof str!=="string")throw`${str} is not a String.`;if(isZero(str))return BigInt(0);let[int,dec]=[str,"00"];if(str.includes(",")){[int,dec]=str.split(",");}else if(str.includes(".")){[int,dec]=str.split(".");}
if(dec.length!==2){dec=(dec+"00").slice(0,2);}
return BigInt(int+dec);}
w.PopStateHandlers["currencyConverter"]=(e)=>setAllFields(strToBigInt(e.state["euro"]));const setEuroParam=(euroVal,push)=>setURLParam("euro",euroVal,{"euro":euroVal},"currencyConverter",push);function setAllFields(euroValue,ignored){setEuroParam(getDisplayValue(euroValue),false);for(let i=0;i<4;i++){const value=getDisplayValue(euroValue*factors[i]);fields[i].placeholder=value;if(i!==ignored)fields[i].value=value;}}
const updateOutput=()=>{output.value=(fields[0].value+" Euro, das sind ja "
+fields[1].value+" Mark; "
+fields[2].value+" Ostmark und "
+fields[3].value+" Ostmark auf dem Schwarzmarkt!");}
function onSubmit(){for(const feld of fields)
feld.value=getDisplayValue(feld.value);setEuroParam(fields[0].value,true);updateOutput();}
for(let i=0;i<4;i++){fields[i].oninput=()=>{for(const field of fields)field.className="";if(!numberRegex.test(fields[i].value)){fields[i].className="invalid";return;}
setAllFields(strToBigInt(fields[i].value)/factors[i],i);updateOutput();}}
for(const field of fields)
field.value=field.placeholder;const form=elById("form");form.action="javascript:void(0)";form.onsubmit=()=>onSubmit();})();
// @license-end
