// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
function startQuotes(currId, nextId) {
    const thisQuoteId = [currId];
    const nextQuoteId = [nextId];
    const params = window.location.search;
    const nextButton = document.getElementById("next");
    const upvoteButton = document.getElementById("upvote");
    const downvoteButton = document.getElementById("downvote");

    const keys = (() => {
        let k = new URLSearchParams(params).get("keys");
        if (!(k && k.length)) {
            return "WASD";
        }  // for vim-like set keys to khjl
        if (k.length === 4) {
            return k.toUpperCase();
        } else {
            alert("Invalid keys given, using default.");
            return "WASD";
        }
    })();  // currently only letter keys are supported
    document.getElementById("wasd").innerText = (
        `${keys[0]} (Upvote), ${keys[2]} (Downvote), `
        + `${keys[1]} (Previous) and ${keys[3]} (Next)`
    );

    document.addEventListener("keydown", function (event) {
        if (event.code === `Key${keys[0]}`) {
            upvoteButton.click();
        } else if (event.code === `Key${keys[1]}`) {
            window.history.back();
        } else if (event.code === `Key${keys[2]}`) {
            downvoteButton.click();
        } else if (event.code === `Key${keys[3]}`) {
            nextButton.click();
        }
    });

    const shareButton = document.getElementById("share");
    const downloadButton = document.getElementById("download");

    const author = document.getElementById("author");
    const quote = document.getElementById("quote");

    const ratingText = document.getElementById("rating-text");
    const ratingImageContainer = document.getElementById(
        "rating-img-container"
    );

    nextButton.removeAttribute("href");

    function updateQuoteId(quoteId) {
        shareButton.href = `/zitate/share/${quoteId}/${params}`;
        downloadButton.href = `/zitate/${quoteId}/image.gif${params}`;
        const [q_id, a_id] = quoteId.split("-", 2);
        quote.href = `/zitate/info/z/${q_id}/${params}`;
        author.href = `/zitate/info/a/${a_id}/${params}`;
        thisQuoteId[0] = quoteId;
        if (window.dynLoadReplaceHrefOnAnchor) {
            for (const anchor of [shareButton, quote, author])
                dynLoadReplaceHrefOnAnchor(anchor);
        }
    }

    function updateRating(rating) {
        rating = rating.toString()
        ratingText.innerText = rating;
        if (["---", "???", "0"].includes(rating)) {
            ratingImageContainer.innerHTML = "";
        } else {
            const ratingNum = Number.parseInt(rating);
            const ratingImg = document.createElement("div")
            ratingImg.className = "rating-img" + (
                ratingNum > 0 ? " witzig" : " nicht-witzig"
            );
            ratingImageContainer.innerHTML = (
                ratingImg.outerHTML + " "
            ).repeat(Math.min(4, Math.abs(ratingNum)));
        }
    }

    function updateVote(vote) {
        if (vote === 1) {
            // now voted up
            upvoteButton.classList.add("voted");
            upvoteButton.value = "0";
        } else {
            upvoteButton.classList.remove("voted");
            upvoteButton.value = "1";
        }
        if (vote === -1) {
            // now voted down
            downvoteButton.classList.add("voted");
            downvoteButton.value = "0";
        } else {
            downvoteButton.classList.remove("voted");
            downvoteButton.value = "-1";
        }
    }

    function handleData(data) {
        if (data["status"]) {
            console.error(data)
            if (data["status"] in [429, 420]) {
                alert(data["reason"]);
            }
        } else if (data && data["id"]) {
            updateQuoteId(data["id"]);
            nextQuoteId[0] = data["next"];
            quote.innerText = `»${data["quote"]}«`;
            author.innerText = `- ${data["author"]}`;
            updateRating(data["rating"]);
            updateVote(Number.parseInt(data["vote"]));
            return true;
        }
    }

    window.PopStateHandlers["quotes"] = (event) => (
        event.state && handleData(event.state)
    )

    nextButton.onclick = () => get(
        `/api/zitate/${nextQuoteId[0]}/`,
        params,
        (data) => {
            if (handleData(data)) {
                data["stateType"] = "quotes";
                window.history.pushState(
                    data,
                    "Falsche Zitate",
                    `/zitate/${data["id"]}/${params}`
                )
            }
        }
    );

    function vote(vote) {
        post(
            `/api/zitate/${thisQuoteId[0]}/`,
            {"vote": vote},
            (data) => handleData(data)
        );
    }

    function setDisabledOfVoteButtons(disabled) {
        upvoteButton.disabled = disabled;
        downvoteButton.disabled = disabled;
    }

    for (const voteButton of [upvoteButton, downvoteButton]) {
        voteButton.type = "button";
        voteButton.onclick = () => {
            setDisabledOfVoteButtons(true);
            vote(voteButton.value);
            setDisabledOfVoteButtons(false);
        }
    }
}
// @license-end
