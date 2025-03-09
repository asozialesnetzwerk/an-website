// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import {
    d,
    e as getElementById,
    get,
    PopStateHandlers,
    post,
    setLastLocation,
} from "@utils/utils.js";

function startQuotes() {
    const nextButton = getElementById("next") as HTMLAnchorElement;
    const upvoteButton = getElementById("upvote") as HTMLButtonElement;
    const downvoteButton = getElementById(
        "downvote",
    ) as HTMLButtonElement;
    const reportButton = getElementById("report") as
        | HTMLAnchorElement
        | null;

    const thisQuoteId = [
        (getElementById("top")!).getAttribute("quote-id")!,
    ];
    const nextQuoteId = [nextButton.getAttribute("quote-id")!];
    const params = location.search;

    const keys = (() => {
        const k = new URLSearchParams(params).get("keys");
        if (!(k?.length)) {
            return "WASD";
        }
        // for vim-like set keys to khjl
        if (k.length === 4) {
            return k.toUpperCase();
        } else {
            alert("Invalid keys given, using default.");
            return "WASD";
        }
    })(); // currently only letter keys are supported

    (getElementById("wasd")!).innerText =
        `${keys[0]} (Witzig), ${keys[2]} (Nicht Witzig), ` +
        `${keys[1]} (Vorheriges) und ${keys[3]} (Nächstes)`;

    d.onkeydown = (event) => {
        switch (event.code) {
            case `Key${keys[0]}`:
                upvoteButton.click();
                break;
            case `Key${keys[1]}`:
                history.back();
                break;
            case `Key${keys[2]}`:
                downvoteButton.click();
                break;
            case `Key${keys[3]}`:
                nextButton.click();
        }
    };

    const shareButton = getElementById("share") as HTMLAnchorElement;
    const downloadButton = getElementById(
        "download",
    ) as HTMLAnchorElement;

    const author = getElementById("author") as HTMLAnchorElement;
    const quote = getElementById("quote") as HTMLAnchorElement;
    const realAuthor = getElementById(
        "real-author-name",
    ) as HTMLAnchorElement;

    const ratingText = getElementById("rating-text") as HTMLDivElement;
    const ratingImageContainer = getElementById(
        "rating-img-container",
    ) as HTMLDivElement;

    nextButton.removeAttribute("href");

    function updateQuoteId(quoteId: string): void {
        shareButton.href = `/zitate/share/${quoteId}${params}`;
        downloadButton.href = `/zitate/${quoteId}.gif${params}`;
        const [q_id, a_id] = quoteId.split("-", 2);
        quote.href = `/zitate/info/z/${q_id}${params}`;
        author.href = `/zitate/info/a/${a_id}${params}`;
        thisQuoteId[0] = quoteId;
    }

    function updateRating(rating: number | string) {
        rating = rating.toString();
        ratingText.replaceChildren(rating);
        if (["---", "???", "0"].includes(rating)) {
            ratingImageContainer.replaceChildren("");
            return;
        }
        const ratingNum = Number.parseInt(rating);
        const className = `rating-img ${
            ratingNum > 0 ? "witzig" : "nicht-witzig"
        }`;
        ratingImageContainer.replaceChildren(
            ...Array
                .from({ length: Math.min(4, Math.abs(ratingNum)) }, () => 1)
                .map(() => <div className={className} />),
        );
    }

    function updateVote(vote: number | string): void {
        function update(
            btn: HTMLButtonElement,
            btn_vote: number,
            btn_vote_str: string,
        ) {
            btn.disabled = false;
            if (vote === btn_vote || vote === btn_vote_str) {
                // the vote of the button is active
                btn.setAttribute("voted", btn_vote_str);
                btn.value = "0"; // if pressed again reset the vote
            } else {
                // the vote of the button isn't active
                btn.removeAttribute("voted");
                btn.value = btn_vote_str; // if pressed, vote with the button
            }
        }
        // update the upvote button
        update(upvoteButton, 1, "1");
        // update the downvote button
        update(downvoteButton, -1, "-1");
    }

    interface API_DATA {
        // either this
        status: number | undefined;
        reason: string;
        // or the following
        id: string;
        rating: string;
        vote: number;
        quote: string;
        author: string;
        real_author: string;
        real_author_id: number;
        next: string;
    }

    function handleData(
        data: API_DATA,
    ): boolean {
        if (data.status) {
            console.error(data);
            if (data.status in [429, 420]) {
                // ratelimited
                alert(data.reason);
            }
            return false;
        } else if (data.id) {
            updateQuoteId(data.id);
            nextQuoteId[0] = data.next;
            quote.innerText = `»${data.quote}«`;
            author.innerText = `- ${data.author}`;
            realAuthor.innerText = data.real_author;
            realAuthor.href = `/zitate/info/a/${data.real_author_id}${params}`;
            if (reportButton?.href) {
                const reportHrefParams = new URLSearchParams(params);
                reportHrefParams.set(
                    "subject",
                    `Das falsche Zitat ${data.id} hat ein Problem`,
                );
                reportHrefParams.set(
                    "message",
                    `${quote.innerText} ${realAuthor.innerText}`,
                );
                reportButton.href = `/kontakt?${reportHrefParams.toString()}`;
            }
            updateRating(data.rating);
            updateVote(data.vote);
            return true;
        }
        return false;
    }

    PopStateHandlers["quotes"] = (event: PopStateEvent) => {
        if (event.state) {
            handleData(event.state as API_DATA);
        }
    };

    interface POP_STATE_API_DATA extends API_DATA {
        stateType: string;
        url: string;
    }

    nextButton.onclick = () =>
        get(
            `/api/zitate/${nextQuoteId[0]}`,
            params,
            (data: POP_STATE_API_DATA) => {
                if (!handleData(data)) {
                    return;
                }

                data.stateType = "quotes";
                data.url = `/zitate/${data.id}${params}`;
                history.pushState(data, "Falsche Zitate", data.url);
                setLastLocation(data.url);
            },
        );

    const vote = (vote: string): Promise<void> =>
        post(
            `/api/zitate/${thisQuoteId[0]}`,
            { vote },
            (data: API_DATA) => void handleData(data),
        );

    for (const voteButton of [upvoteButton, downvoteButton]) {
        voteButton.type = "button";
        voteButton.onclick = () => {
            upvoteButton.disabled = true;
            downvoteButton.disabled = true;
            vote(voteButton.value)
                .then(() => {
                    upvoteButton.disabled = false;
                    downvoteButton.disabled = false;
                })
                .catch(() => {
                    upvoteButton.disabled = false;
                    downvoteButton.disabled = false;
                });
        };
    }
}

for (
    const autoSubmitEl of (d.getElementsByClassName(
        "auto-submit-element",
    ) as HTMLCollectionOf<HTMLInputElement>)
) {
    autoSubmitEl.onchange = () => {
        (autoSubmitEl.form!).submit();
    };
}

startQuotes();
