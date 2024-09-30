// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
const openPane = document.getElementById("open-pane");
const sitePane = document.getElementById("site-pane");

if (!openPane || !sitePane) {
    throw Error("open-pane or site-pane not found");
}

function setSitePaneState(state: "open" | "close") {
    console.debug(`${state} sitePane`);
    sitePane?.setAttribute("state", state);
}

export function showSitePane() {
    setSitePaneState("open");
}
export function hideSitePane() {
    setSitePaneState("close");
}

const belongsToSitePane = (el: HTMLElement) => (
    el === openPane || el === sitePane || sitePane.contains(el)
);

// mouse users
openPane.onmouseover = showSitePane;
sitePane.onmouseleave = hideSitePane;

// keyboard users
document.onfocus = (event: FocusEvent) => {
    if (belongsToSitePane(event.target as HTMLElement)) {
        showSitePane();
    } else {
        hideSitePane();
    }
};

// phone users
openPane.onclick = showSitePane;
document.onclick = (e: Event) => {
    if (!belongsToSitePane(e.target as HTMLElement)) {
        hideSitePane();
    }
};

// swipe gestures (for phone users)
const startPos: { x: number | null; y: number | null } = {
    x: null,
    y: null,
};
document.ontouchstart = (e: TouchEvent) => {
    // save start pos of touch
    startPos.x = e.touches[0]?.clientX ?? null;
    startPos.y = e.touches[0]?.clientY ?? null;
};
document.ontouchmove = (e: TouchEvent) => {
    if (startPos.x === null || startPos.y === null) {
        return;
    }
    // calculate difference
    const diffX = startPos.x - (e.touches[0]?.clientX ?? 0);
    const diffY = startPos.y - (e.touches[0]?.clientY ?? 0);

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
};
