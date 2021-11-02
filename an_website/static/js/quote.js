// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
/*
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

const nextButton = document.getElementById("next");

const upvoteButton = document.getElementById("upvote");
const downvoteButton = document.getElementById("downvote");

document.addEventListener("keydown", function(event) {
    if(event.code === "ArrowUp" || event.code === "KeyW") {
        upvoteButton.click();
    } else if(event.code === "ArrowLeft" || event.code === "KeyA") {
        window.history.back();
    } else if(event.code === "ArrowDown" || event.code === "KeyS") {
        downvoteButton.click();
    } else if(event.code === "ArrowRight" || event.code === "KeyD") {
        nextButton.click();
    }
});


const shareButton = document.getElementById("share");
const downloadButton = document.getElementById("download");

const author = document.getElementById("author");
const quote = document.getElementById("quote");

const ratingText = document.getElementById("rating-text");
const ratingImg = document.getElementById("rating-image");

const params = nextButton.href.includes("?")
    ? "?" + nextButton.href.split("?", 2)[1]
    : "";

nextButton.removeAttribute("href");

function updateQuoteId(quoteId) {
    shareButton.href = `/zitate/${quoteId}/share/${params}`;
    downloadButton.href = `/zitate/${quoteId}/image.png${params}`;
    const [q_id, a_id] = quoteId.split("-", 2);
    quote.href = `/zitate/info/q/${q_id}/${params}`;
    author.href = `/zitate/info/a/${a_id}/${params}`;

    thisQuoteId[0] = quoteId;
}

function updateRating(rating) {
    ratingText.innerText = rating;
    if (rating === "---" || rating === 0) {
        ratingImg.className = "invisible";
        ratingImg.src = "";
        ratingImg.alt = "";
    } else if (Number.parseInt(rating) > 0) {
        ratingImg.className = "witzig";
        ratingImg.src = "/static/img/StempelWitzigKlein.svg";
        ratingImg.alt = "Witzig-Stempel";
    } else if (Number.parseInt(rating)  < 0) {
        ratingImg.className = "nicht-witzig";
        ratingImg.src = "/static/img/StempelNichtWitzigKlein.svg";
        ratingImg.alt = "Nicht-Witzig-Stempel";
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
    fetch(`/zitate/api/${nextQuoteId[0]}/${params}`)
        .then((response) => response.json())
        .then((data) => {
            if (handleData(data)) {
                window.history.pushState(
                    data,
                    "Falsche Zitate",
                    `/zitate/${data["id"]}/${params}`
                );
            }
        }).catch(function(error) {
            console.error(error);
        });
}

function vote(vote) {
    fetch(`/zitate/api/${thisQuoteId[0]}/`, {
        method: "post",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `vote=${vote}`
    }).then(response => response.json())
        .then(data =>  handleData(data))
        .catch(error => {
            console.error(error)
        });
}

for (const voteButton of [upvoteButton, downvoteButton]) {
    voteButton.type = "button";
    voteButton.onclick = () => {
        vote(voteButton.value);
    }
}
// @license-end
