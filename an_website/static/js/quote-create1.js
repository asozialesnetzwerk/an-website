// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const quoteInput = document.getElementById("quote-input");
const quoteList = document.getElementById("quote-list");
const realAuthorInput = document.getElementById("real-author-input");

quoteInput.oninput = () => {
    // console.log(quoteInput);
    for (let child of quoteList.children) {
        if (child.value === quoteInput.value) {
            // console.log(child);
            realAuthorInput.value = child.attributes.getNamedItem("author").value;
            realAuthorInput.disabled = true;
            return;
        }
    }
    // Not found in data list, enable real author input again.
    realAuthorInput.disabled = false;
}
// @license-end
