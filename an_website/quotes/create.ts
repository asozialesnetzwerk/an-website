// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
export {};

const realAuthors: any = {};
for (
    const child
        of (document.getElementById("quote-list") as HTMLDataListElement)
            .children
) {
    // put the quotes with their authors into an object
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    realAuthors[
        (child as unknown as { value: string }).value.toLowerCase()
    ] = ((child as { attributes: NamedNodeMap })
        .attributes
        .getNamedItem("data-author")!)
        .value;
}

const quoteInput = document.getElementById("quote-input") as HTMLInputElement;
const realAuthorInput = document.getElementById(
    "real-author-input",
) as HTMLInputElement;
quoteInput.oninput = () => {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const author = realAuthors[quoteInput.value.toLowerCase()] as
        | string
        | undefined;
    // when real author is found disable input and set the value
    realAuthorInput.disabled = !!author; // !! ≙ check of truthiness
    if (author) {
        realAuthorInput.value = author;
    }
};
// @license-end
