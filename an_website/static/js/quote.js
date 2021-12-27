// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
const nextButton = document.getElementById("next");

const upvoteButton = document.getElementById("upvote");
const downvoteButton = document.getElementById("downvote");

const keys = (() => {
    let k = new URLSearchParams(window.location.search).get("keys");
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
    `${keys[0]} (Upvote), ${keys[2]} (Downvote), ${keys[1]} (Previous) and ${keys[3]} (Next)`
);

document.addEventListener("keydown", function(event) {
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
const ratingImageContainer = document.getElementById("rating-img-container");

const params = window.location.search;

nextButton.removeAttribute("href");

function updateQuoteId(quoteId) {
    shareButton.href = `/zitate/${quoteId}/share/${params}`;
    downloadButton.href = `/zitate/${quoteId}/image.png${params}`;
    const [q_id, a_id] = quoteId.split("-", 2);
    quote.href = `/zitate/info/z/${q_id}/${params}`;
    author.href = `/zitate/info/a/${a_id}/${params}`;

    thisQuoteId[0] = quoteId;
}

function updateRating(rating) {
    ratingText.innerText = rating;
    const ratingImg = document.createElement("div")
    if (rating === "---" || rating === "???" || rating === 0) {
        ratingImageContainer.innerHTML = "";
    } else {
        const ratingNum = Number.parseInt(rating);
        if (ratingNum > 0) {
            ratingImg.className = "rating-img witzig";
        } else if (ratingNum  < 0) {
            ratingImg.className = "rating-img nicht-witzig";
        }
        ratingImageContainer.innerHTML = (ratingImg.outerHTML + " ").repeat(Math.min(4, Math.abs(ratingNum)));
    }
}

function updateVote(vote) {
    if (vote === 1) {
        upvoteButton.classList.add("voted");
        upvoteButton.value = "0";
    } else {
        upvoteButton.classList.remove("voted");
        upvoteButton.value = "1";
    }
    if (vote === -1) {
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
        if (data["status"] === 429 || data["status"] === 420) {
            alert(data["reason"]);
        }
        return false;
    } else if (typeof data !== "undefined" && typeof data["id"] !== "undefined") {
        updateQuoteId(data["id"]);
        nextQuoteId[0] = data["next"];
        quote.innerText = `»${data["quote"]}«`;
        author.innerText = `- ${data["author"]}`;
        updateRating(data["rating"]);
        updateVote(data["vote"]);
        return true;
    }
}

window.onpopstate = (event) => {
    const data = event.state;
    if (data) {
        handleData(data);
    }
}

nextButton.onclick = () => {
    get(
        `/api/zitate/${nextQuoteId[0]}/`,
        params,
        (data) => {
            if (handleData(data)) {
                window.history.pushState(
                    data,
                    "Falsche Zitate",
                    `/zitate/${data["id"]}/${params}`
                );
            }
        }
    )
}

function vote(vote) {
    post(
        `/api/zitate/${thisQuoteId[0]}/`,
        {
            "vote": vote
        },
        (data) => {
            handleData(data)
        }
    );
}

for (const voteButton of [upvoteButton, downvoteButton]) {
    voteButton.type = "button";
    voteButton.onclick = () => {
        vote(voteButton.value);
    }
}
// @license-end
