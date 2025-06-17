// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import { e as getElementById } from "@utils/utils.js";

const messageInput = getElementById(
    "message-input",
) as HTMLInputElement;
const messageInputForm = messageInput.form!;
const messageSection = getElementById("message-section")!;
const usingOpenMoji = getElementById("openmoji-attribution");
const openmojiVersion = usingOpenMoji?.getAttribute("openmoji-version");
let reconnectTimeout = 100;
let reconnectTries = 0;
let lastMessage = "";

const timeStampToText = (timestamp: number) => {
    return new Date(timestamp + 1651075200000).toLocaleString();
};

const getOpenMojiType = () => usingOpenMoji?.getAttribute("type");

interface Message {
    author: string[];
    content: string[];
    timestamp: number;
}

const EmojiImgComponent = ({ emoji }: { emoji: string }): JSX.Element => {
    // eslint-disable-next-line @typescript-eslint/no-misused-spread
    const chars = [...emoji];
    const emojiCode = (
        chars.length == 2 && chars[1] === "\uFE0F" ? [chars[0]!] : chars
    )
        .map((e: string) => e.codePointAt(0)!.toString(16).padStart(4, "0"))
        .join("-")
        .toUpperCase();

    const path = `/static/openmoji/svg/${emojiCode}.svg`;
    return (
        <img
            src={openmojiVersion ? `${path}?v=${openmojiVersion}` : path}
            alt={emoji}
            className="emoji"
        />
    );
};

const EmojiComponent = ({ emoji }: { emoji: string }): JSX.Element => {
    console.log(getOpenMojiType());
    if (getOpenMojiType() === "img") {
        return <EmojiImgComponent emoji={emoji} />;
    }
    if (getOpenMojiType()) {
        return <span className="openmoji">{[emoji]}</span>;
    }
    return emoji;
};

const MessageComponent = ({ msg }: { msg: Message }): JSX.Element => (
    <div tooltip={timeStampToText(msg.timestamp)}>
        <>
            {msg
                .author
                .map((emoji) => <EmojiComponent emoji={emoji} />)}
        </>
        {": "}
        <>
            {msg
                .content
                .map((emoji) => <EmojiComponent emoji={emoji} />)}
        </>
    </div>
);

const appendMessage = (msg: Message) => {
    messageSection.append(<MessageComponent msg={msg} />);
};

const displayCurrentUser = (name: string[]) => {
    const id = "current-user";
    getElementById(id)!.replaceWith(
        <div className={getOpenMojiType() ? "openmoji" : ""} id={id}>
            {name.map((emoji) => <EmojiComponent emoji={emoji} />)}
        </div>,
    );
};

const resetLastMessage = () => {
    if (lastMessage && !messageInput.value) {
        messageInput.value = lastMessage;
        lastMessage = "";
    }
};

type ConnectionState = "connecting" | "connected" | "disconnected";

const stateMapping: Record<ConnectionState, string> = {
    connecting: "Versuche mit WebSocket zu verbinden",
    connected: "Mit WebSocket verbunden!",
    disconnected: "Verbindung getrennt. Drücke hier um erneut zu versuchen.",
};

const setConnectionState = (state: ConnectionState) => {
    const id = "connection-state";

    const onclick = state == "disconnected"
        ? (() => {
            reconnectTries = 0;
            reconnectTimeout = 500;
            getElementById(id)!.removeEventListener("click", onclick!);
            openWS();
        })
        : undefined;

    getElementById(id)!.replaceWith(
        <div
            tooltip={stateMapping[state]}
            tooltip-position="right"
            onclick={onclick}
            data-state={state}
            id={id}
        />,
    );
};

const handleWebSocketData = (event: { data: string }) => {
    const data = JSON.parse(event.data) as {
        type: string;
        // the following are only present depending on the type
        message: Message;
        messages: Message[];
        current_user: string[];
        retry_after: number;
        users: string[];
        error: string;
    };
    switch (data.type) {
        case "messages": {
            messageSection.innerText = "";
            for (const msg of data.messages) {
                appendMessage(msg);
            }
            break;
        }
        case "message": {
            // console.debug("New message", data["message"]);
            appendMessage(data.message);
            break;
        }
        case "init": {
            displayCurrentUser(data.current_user);
            console.log("Connected as", data.current_user.join(""));
            setConnectionState("connected");
            reconnectTimeout = 100;
            reconnectTries = 0;
            break;
        }
        case "users": {
            // only gets sent in dev mode of website
            console.debug("Received users data", data.users);
            break;
        }
        case "ratelimit": {
            resetLastMessage();
            // TODO: Don't use alert
            alert(`Retry after ${data.retry_after} seconds.`);
            break;
        }
        case "error": {
            resetLastMessage();
            alert(data.error); // TODO: Don't use alert
            break;
        }
        default: {
            console.error(`Invalid type ${data.type}`);
        }
    }
};

const openWS = () => {
    setConnectionState("connecting");
    const ws = new WebSocket(
        (location.protocol === "https:" ? "wss:" : "ws:") +
            `//${location.host}/websocket/emoji-chat`,
    );
    const pingInterval = setInterval(() => {
        if (ws.readyState == ws.OPEN) {
            ws.send("");
        }
    }, 10000);

    ws.addEventListener("close", (event) => {
        clearInterval(pingInterval);
        if (event.wasClean) {
            console.debug(
                `Connection closed cleanly, code=${event.code} reason=${event.reason}`,
            );
            setConnectionState("disconnected");
            return;
        }
        console.debug(
            `Connection closed, reconnecting in ${reconnectTimeout}ms  (${reconnectTries})`,
        );
        setConnectionState("connecting");
        if (reconnectTries > 10) {
            // not connected for long time, just give up
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
    });

    ws.addEventListener("open", (event) => {
        setConnectionState("connected");
        console.debug("Opened WebSocket", event);
    });

    ws.addEventListener("error", (event) => {
        console.error({ msg: "got error from websocket", event });
    });

    ws.addEventListener("message", (event) => {
        handleWebSocketData(event);
    });

    messageInputForm.addEventListener("submit", (event) => {
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
    });
};
openWS();
