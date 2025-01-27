import { post, e as getElementById } from "@utils/utils.js";

interface Reasoned {
    reason?: string;
}

type Data = {
    author_id: number,
    quote_id: number,
} | {
    author_id: number,
} | {
    quote_id: number,
};

function getDataFromUrl(): Data {
    const path: string[] = location.pathname.split('/');
    console.debug(path);
    if (path[path.length - 1] == "") {
        path.pop();
    }
    const infoIndex = path.indexOf("info");
    const last = path.pop()!;
    if (infoIndex == -1) {
        const [quote_id, author_id] = last.split("-", 2).map(Number);
        return { quote_id: quote_id!, author_id: author_id! };
    }
    const type = path[infoIndex + 1];
    if (type == "z") {
        return { quote_id: Number(last) };
    }
    if (type == "a") {
        return { quote_id: Number(last) };
    }
    console.error({ msg: "invalid path", path });
    throw new Error("Invalid state");
}

function createReportButton(anchor: HTMLAnchorElement) {
    anchor.removeAttribute('href')
    anchor.addEventListener("click", (event: Event) => {
        event.preventDefault();
        const data: Data & Reasoned = getDataFromUrl();
        const reason = prompt("Grund fürs Melden?", "");
        if (reason === null) {
            console.debug("Aborted");
            return;
        }
        if (reason) {
            console.debug("Provided reason: " + reason);
            data.reason = reason;
        }
        void reportQuote(data);
    });
}

function reportQuote(reportData: Data & Reasoned): Promise<void> {
    console.debug({ msg: "reporting", reportData });
    return post(
        "/api/zitate/melden",
        reportData,
        (data: boolean) => {
            if (data) {
                alert("Erfolgreich gemeldet!")
            }
        }
    );
}

createReportButton(getElementById("report")! as HTMLAnchorElement);
