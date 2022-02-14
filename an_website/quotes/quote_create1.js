// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
(() => {
    const quoteInput = elById("quote-input");
    const quoteList = elById("quote-list");
    const realAuthorInput = elById("real-author-input");

    const realAuthors = {};
    for (let child of quoteList.children) {
        // put the quotes with their authors into an object
        realAuthors[child.value.toLowerCase()] = child.attributes.getNamedItem("data-author").value;
    }

    quoteInput.oninput = () => {
        const author = realAuthors[quoteInput.value.toLowerCase()];
        // when real author is found disable input and set the value
        realAuthorInput.disabled = !!author;
        if (author) realAuthorInput.value = author;
    }
})();
// @license-end
