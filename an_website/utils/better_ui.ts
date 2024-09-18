// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
// these functions break if using the CSS-only functionality of the site-pane
export function showSitePane() {
    document.getElementById("site-pane")?.setAttribute("open", "");
}
export function hideSitePane() {
    document.getElementById("site-pane")?.removeAttribute("open");
}

const openPane = document.getElementById("open-pane");
const sitePane = document.getElementById("site-pane");

if (!openPane || !sitePane) {
    throw Error("open-pane or site-pane not found");
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
document.onclick = (e) => {
    belongsToSitePane(e.target as HTMLElement) || hideSitePane();
};

// swipe gestures (for phone users)
const startPos: { x: number | null; y: number | null } = {
    x: null,
    y: null,
};
document.ontouchstart = (e) => {
    // save start pos of touch
    // @ts-expect-error TS2532
    startPos.x = e.touches[0].clientX;
    // @ts-expect-error TS2532
    startPos.y = e.touches[0].clientY;
};
document.ontouchmove = (e) => {
    if (startPos.x === null || startPos.y === null) {
        return;
    }
    // calculate difference
    // @ts-expect-error TS2532
    const diffX = startPos.x - e.touches[0].clientX;
    // @ts-expect-error TS2532
    const diffY = startPos.y - e.touches[0].clientY;

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
        diffX > 0 ? showSitePane() : hideSitePane();
    }
};
