// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(() => {
    const messageInput = elById("message-input");
    const messageSection = elById("message-section");
    const usingOpenMoji = elById("open-moji-attribution");

    function appendMessage(msg) {
        let el = document.createElement("div");
        if (usingOpenMoji && usingOpenMoji.getAttribute("type") !== "font") {
            for (let emoji of msg.author) {
                el.append(emojiToIMG(emoji));
            }
            el.innerHTML += ": ";
            for (let emoji of msg.content) {
                el.append(emojiToIMG(emoji));
            }
        } else {
            el.innerText = `${msg.author.join('')}: ${msg.content.join('')}`;
        }

        el.setAttribute("timestamp", msg.timestamp);
        messageSection.append(el);
    }

    function emojiToIMG(emoji) {
        let emojiCode = [...emoji].map(e => e.codePointAt(0).toString(16)).join(`-`).toUpperCase();

        let imgEl = document.createElement("img");

        imgEl.src = `/static/img/openmoji-svg-14.0/${emojiCode}.svg`;
        imgEl.classList.add("emoji")
        imgEl.alt = emoji;

        return imgEl;
    }

    let ws = new WebSocket(
        (w.location.protocol === "https:" ? "wss:" : "ws:")
        + `//${w.location.host}/websocket/emoji-chat`
    );
    ws.onclose = (event) => {
        if (event.wasClean) {
            console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            alert("Connection died, pls reload the page.");
        }
    };
    setInterval(() => ws.send(""), 10_000)
    ws.onopen = (event) => {
        console.log("Opened WebSocket", event)
    };
    ws.onmessage =  (evt) => {
        const data = JSON.parse(evt.data)
        switch (data["type"]) {
            case "messages": {
                messageSection.innerText = "";
                for (let msg of data["messages"]) {
                    appendMessage(msg);
                }
                break;
            }
            case "message": {
                console.debug("New message", data["message"]);
                appendMessage(data["message"]);
                break;
            }
            case "users": {
                console.log(data["current_user"], data["users"]);
                break;
            }
            case "error": {
                alert(data["error"]);
                break;
            }
            default: {
                console.error(`Invalid type ${data["type"]}`);
            }
        }
    };

    messageInput.form.onsubmit = (event) => {
        if (messageInput.value !== "") {
            ws.send(
                JSON.stringify(
                    {
                        "type": "message",
                        "message": messageInput.value,
                    }
                )
            );
            messageInput.value = "";
        }
        event.preventDefault();
    }
})();
// @license-end
