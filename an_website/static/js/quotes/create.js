"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(()=>{const e={};for(const t of elById("quote-list").children)e[t.value.toLowerCase()]=t.attributes.getNamedItem("data-author").value;const u=elById("quote-input"),a=elById("real-author-input");u.oninput=()=>{const t=e[u.value.toLowerCase()];a.disabled=!!t,t&&(a.value=t)}})();// @license-end
//# sourceMappingURL=create.js.map
