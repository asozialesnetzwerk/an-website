// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
function startQuotes() {
    const nextButton = elById("next");
    const upvoteButton = elById("upvote");
    const downvoteButton = elById("downvote");
    // may be missing
    const reportButton = elById("report");

    const thisQuoteId = [elById("top").getAttribute("quote-id")];
    const nextQuoteId = [nextButton.getAttribute("quote-id")];
    const params = w.location.search;


    const keys = (() => {
        let k = new URLSearchParams(params).get("keys");
        if (!(k && k.length))
            return "WASD";
        // for vim-like set keys to khjl
        if (k.length === 4) {
            return k.toUpperCase();
        } else {
            alert("Invalid keys given, using default.");
            return "WASD";
        }
    })();  // currently only letter keys are supported
    elById("wasd").innerText = (
        `${keys[0]} (Witzig), ${keys[2]} (Nicht Witzig), `
        + `${keys[1]} (Vorheriges) und ${keys[3]} (Nächstes)`
    );

    d.onkeydown = (event) => {
        switch (event.code) {
            case `Key${keys[0]}`:
                upvoteButton.click();
                break;
            case `Key${keys[1]}`:
                w.history.back();
                break;
            case `Key${keys[2]}`:
                downvoteButton.click();
                break;
            case `Key${keys[3]}`:
                nextButton.click();
        }
    };

    const shareButton = elById("share");
    const downloadButton = elById("download");

    const author = elById("author");
    const quote = elById("quote");
    const realAuthor = elById("real-author-name");

    const ratingText = elById("rating-text");
    const ratingImageContainer = elById("rating-img-container");

    nextButton.removeAttribute("href");

    function updateQuoteId(quoteId) {
        shareButton.href = fixHref(`/zitate/share/${quoteId}${params}`);
        downloadButton.href = fixHref(`/zitate/${quoteId}.gif${params}`);
        const [q_id, a_id] = quoteId.split("-", 2);
        quote.href = fixHref(`/zitate/info/z/${q_id}${params}`);
        author.href = fixHref(`/zitate/info/a/${a_id}${params}`);
        thisQuoteId[0] = quoteId;
    }

    function updateRating(rating) {
        rating = rating.toString()
        ratingText.innerText = rating;
        if (["---", "???", "0"].includes(rating)) {
            ratingImageContainer.innerHTML = "";
            return;
        }
        const ratingNum = Number.parseInt(rating);
        const ratingImg = d.createElement("div")
        ratingImg.className = "rating-img" + (
            ratingNum > 0 ? " witzig" : " nicht-witzig"
        );
        ratingImageContainer.innerHTML = (
            ratingImg.outerHTML + " "
        ).repeat(Math.min(4, Math.abs(ratingNum))).trim();
    }

    function updateVote(vote) {
        function update(btn, btn_vote, btn_vote_str) {
            btn.disabled = false;
            if (vote === btn_vote) {
                // the vote of the button is active
                btn.setAttribute("voted", btn_vote_str);
                btn.value = "0";  // if pressed again reset the vote
            } else {
                // the vote of the button isn't active
                btn.removeAttribute("voted");
                btn.value = btn_vote_str;  // if pressed, vote with the button
            }
        }
        // update the upvote button
        update(upvoteButton, 1, "1");
        // update the downvote button
        update(downvoteButton, -1, "-1");
    }

    function handleData(data) {
        if (data["status"]) {
            error(data)
            if (data["status"] in [429, 420])
                // ratelimited
                alert(data["reason"]);
        } else if (data && data["id"]) {
            updateQuoteId(data["id"]);
            nextQuoteId[0] = data["next"];
            quote.innerText = `»${data["quote"]}«`;
            author.innerText = `- ${data["author"]}`;
            realAuthor.innerText = data["real_author"];
            realAuthor.href = fixHref(
                `/zitate/info/a/${data["real_author_id"]}${params}`
            );
            if (reportButton) {
                const reportHrefParams = new URLSearchParams(params);
                reportHrefParams.set(
                    "subject", `Das falsche Zitat ${data["id"]} hat ein Problem`
                );
                reportHrefParams.set(
                    "message", `${quote.innerText} ${realAuthor.innerText}`
                );
                reportButton.href = fixHref(`/kontakt?${reportHrefParams}`);
            }
            updateRating(data["rating"]);
            updateVote(Number.parseInt(data["vote"]));
            return true;
        }
    }

    w.PopStateHandlers["quotes"] = (event) => (
        event.state && handleData(event.state)
    )

    nextButton.onclick = () => get(
        `/api/zitate/${nextQuoteId[0]}`,
        params,
        (data) => {
            if (!handleData(data)) return;

            data["stateType"] = "quotes";
            data["url"] = `/zitate/${data["id"]}${params}`;
            w.history.pushState(
                data,
                "Falsche Zitate",
                data["url"]
            )
            w.lastLocation = data["url"];
        }
    );

    const vote = (vote) => post(
        `/api/zitate/${thisQuoteId[0]}`,
        {"vote": vote},
        (data) => handleData(data)
    );

    for (const voteButton of [upvoteButton, downvoteButton]) {
        voteButton.type = "button";
        voteButton.onclick = () => {
            upvoteButton.disabled = true;
            downvoteButton.disabled = true;
            vote(voteButton.value);
            upvoteButton.disabled = false;
            downvoteButton.disabled = false;
        }
    }
}

for (let autoSubmitEl of document.getElementsByClassName("auto-submit-element")) {
    autoSubmitEl.onchange = () => autoSubmitEl.form.submit();
}

startQuotes();
// @license-end
