"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(()=>{const e={};for(const t of elById("quote-list").children)e[t.value.toLowerCase()]=t.attributes.getNamedItem("data-author").value;const a=elById("quote-input"),n=elById("real-author-input");a.oninput=()=>{const t=e[a.value.toLowerCase()];n.disabled=!!t,t&&(n.value=t)}})();// @license-end
//# sourceMappingURL=create.js.map
