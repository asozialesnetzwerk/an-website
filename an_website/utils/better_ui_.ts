// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
type EventHandler<T extends keyof HTMLElementEventMap> = (
    event: HTMLElementEventMap[T],
) => unknown;
const addEventListener = <T extends keyof HTMLElementEventMap>(
    element: HTMLElement,
    type: T,
    fun: EventHandler<T>,
) => {
    element.addEventListener(type, fun);
};

type DocumentEventHandler<T extends keyof DocumentEventMap> = (
    event: DocumentEventMap[T],
) => unknown;
const addDocumentEventListener = <T extends keyof DocumentEventMap>(
    type: T,
    fun: DocumentEventHandler<T>,
) => {
    document.addEventListener(type, fun);
};

const openPane = document.getElementById("open-pane");
const sitePane = document.getElementById("site-pane");

if (!openPane || !sitePane) {
    throw Error("open-pane or site-pane not found");
}

const setSitePaneState = (state: "open" | "close") => {
    console.debug(`${state} sitePane`);
    sitePane.setAttribute("state", state);
};

export const showSitePane = () => {
    setSitePaneState("open");
};
export const hideSitePane = () => {
    setSitePaneState("close");
};

const belongsToSitePane = (el: HTMLElement) => (
    el === openPane || el === sitePane || sitePane.contains(el)
);

// mouse users
addEventListener(openPane, "mouseover", showSitePane);
addEventListener(openPane, "mouseleave", hideSitePane);

// keyboard users
addDocumentEventListener("focusin", (event) => {
    if (belongsToSitePane(event.target as HTMLElement)) {
        console.debug("showing site pane because of focus event", event);
        showSitePane();
    } else {
        console.debug("hiding site pane because of focus event", event);
        hideSitePane();
    }
});
addDocumentEventListener("focusout", (event) => {
    if (belongsToSitePane(event.target as HTMLElement)) {
        console.debug("hiding site pane because of blur event", event);
        hideSitePane();
    } else {
        console.debug("blur event", event);
    }
});

// phone users
addEventListener(openPane, "click", showSitePane);
addDocumentEventListener("click", (event) => {
    if (!belongsToSitePane(event.target as HTMLElement)) {
        hideSitePane();
    }
});

// swipe gestures (for phone users)
const startPos: { x: number | null; y: number | null } = {
    x: null,
    y: null,
};
addDocumentEventListener("touchstart", (event) => {
    // save start pos of touch
    startPos.x = event.touches[0]?.clientX ?? null;
    startPos.y = event.touches[0]?.clientY ?? null;
});
addDocumentEventListener("touchmove", (event) => {
    if (startPos.x === null || startPos.y === null) {
        return;
    }
    // calculate difference
    const diffX = startPos.x - (event.touches[0]?.clientX ?? 0);
    const diffY = startPos.y - (event.touches[0]?.clientY ?? 0);

    // early return if just clicked, not swiped
    if (diffX === 0 && diffY === 0) {
        return;
    }

    // reset start pos
    startPos.x = null;
    startPos.y = null;

    const minDiffX = Math.max(12, 0.01 * screen.width, diffY * 1.5);

    console.debug({ diffX, minDiffX });

    if (Math.abs(diffX) >= minDiffX) {
        if (diffX > 0) {
            showSitePane();
        } else {
            hideSitePane();
        }
    }
});
