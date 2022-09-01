// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
/* eslint-disable @typescript-eslint/no-unsafe-argument */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/restrict-plus-operands */
/* eslint-disable @typescript-eslint/restrict-template-expressions */
"use strict";
(() => {
    const messageInput = elById("message-input") as HTMLInputElement;
    const messageInputForm = messageInput.form as HTMLFormElement;
    const messageSection = elById("message-section") as HTMLElement;
    const usingOpenMoji = elById("open-moji-attribution");
    const connectionIndicator = elById("connection-state") as HTMLElement;
    const currentUser = elById("current-user") as HTMLElement;
    let reconnectTimeout = 100;
    let reconnectTries = 0;
    let lastMessage = "";

    const timeStampToText = (timestamp) => {
        return new Date(timestamp + 1651075200000).toLocaleString();
    };

    const appendMessage = (msg) => {
        const el = document.createElement("div");
        if (usingOpenMoji && usingOpenMoji.getAttribute("type") !== "font") {
            for (const emoji of msg.author) {
                el.append(emojiToIMG(emoji));
            }
            el.innerHTML += ": ";
            for (const emoji of msg.content) {
                el.append(emojiToIMG(emoji));
            }
        } else {
            el.innerText = `${msg.author.join("")}: ${msg.content.join("")}`;
        }

        el.setAttribute("tooltip", timeStampToText(msg.timestamp));
        messageSection.append(el);
    };

    const displayCurrentUser = (name) => {
        currentUser.innerHTML = "";
        if (usingOpenMoji && usingOpenMoji.getAttribute("type") !== "font") {
            for (const emoji of name) {
                currentUser.append(emojiToIMG(emoji));
            }
            return;
        }
        currentUser.innerText = name.join("");
    };

    const emojiToIMG = (emoji) => {
        const emojiCode = [...emoji]
            .map((e) => e.codePointAt(0).toString(16).padStart(4, "0"))
            .join(`-`)
            .toUpperCase();

        const imgEl = document.createElement("img");

        imgEl.src = `/static/img/openmoji-svg-14.0/${emojiCode}.svg`;
        imgEl.classList.add("emoji");
        imgEl.alt = emoji;

        return imgEl;
    };

    const resetLastMessage = () => {
        if (lastMessage && !messageInput.value) {
            messageInput.value = lastMessage;
            lastMessage = "";
        }
    };

    const setConnectionState = (state) => {
        let tooltip;
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        connectionIndicator.onclick = () => {};
        if (state === "connecting") {
            tooltip = "Versuche mit WebSocket zu verbinden";
        } else if (state === "connected") {
            tooltip = "Mit WebSocket verbunden!";
        } else if (state === "disconnected") {
            tooltip =
                "Verbindung getrennt. Drücke hier um erneut zu versuchen.";
            connectionIndicator.onclick = () => {
                reconnectTries = 0;
                reconnectTimeout = 500;
                // eslint-disable-next-line @typescript-eslint/no-empty-function
                connectionIndicator.onclick = () => {};
                openWS();
            };
        } else {
            console.error("invalid state", state);
            return;
        }
        connectionIndicator.setAttribute("state", state);
        connectionIndicator.setAttribute("tooltip", tooltip);
    };

    const handleWebSocketData = (event) => {
        const data = JSON.parse(event.data);
        switch (data["type"]) {
            case "messages": {
                messageSection.innerText = "";
                for (const msg of data["messages"]) {
                    appendMessage(msg);
                }
                break;
            }
            case "message": {
                // console.debug("New message", data["message"]);
                appendMessage(data["message"]);
                break;
            }
            case "init": {
                displayCurrentUser(data["current_user"]);
                console.log("Connected as", data["current_user"].join(""));
                setConnectionState("connected");
                reconnectTimeout = 100;
                reconnectTries = 0;
                break;
            }
            case "users": {
                // only gets send in dev mode of website
                console.debug("Recieved users data", data["users"]);
                break;
            }
            case "ratelimit": {
                resetLastMessage();
                // TODO: Don't use alert
                alert(`Retry after ${data["Retry-After"]} seconds.`);
                break;
            }
            case "error": {
                resetLastMessage();
                alert(data["error"]); // TODO: Don't use alert
                break;
            }
            default: {
                console.error(`Invalid type ${data["type"]}`);
            }
        }
    };

    const openWS = () => {
        setConnectionState("connecting");
        const ws = new WebSocket(
            (window.location.protocol === "https:" ? "wss:" : "ws:") +
                `//${window.location.host}/websocket/emoji-chat`,
        );
        const pingInterval = setInterval(() => ws.send(""), 10000);
        ws.onclose = (event) => {
            // eslint-disable-next-line @typescript-eslint/no-empty-function
            messageInputForm.onsubmit = () => {};
            if (event.wasClean) {
                console.debug(
                    `Connection closed cleanly, code=${event.code} reason=${event.reason}`,
                );
                setConnectionState("disconnected");
                return;
            }
            console.debug(
                `Connection closed, reconnecting in ${reconnectTimeout}ms`,
            );
            setConnectionState("connecting");
            clearInterval(pingInterval);
            if (reconnectTries > 20) {
                // ~3 minutes not connected, just give up
                setConnectionState("disconnected");
                return;
            }
            setTimeout(() => {
                reconnectTimeout = Math.max(
                    500, // minimum 500ms, for a better curve
                    Math.floor(
                        // maximum 15s, so we don't have to wait too long
                        Math.min(15000, 1.5 * reconnectTimeout - 200),
                    ),
                );
                reconnectTries++;
                openWS(); // restart connection
            }, reconnectTimeout);
        };
        ws.onopen = (event) => console.debug("Opened WebSocket", event);
        ws.onmessage = handleWebSocketData;

        messageInputForm.onsubmit = (event) => {
            if (messageInput.value !== "") {
                lastMessage = messageInput.value;
                ws.send(
                    JSON.stringify({
                        type: "message",
                        message: messageInput.value,
                    }),
                );
                messageInput.value = "";
            }
            event.preventDefault();
        };
    };
    openWS();
})();
// @license-end