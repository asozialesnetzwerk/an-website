// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later

// these functions break if used the css-only functionality of the site-pane
function showSitePane() {
    elById("site-pane").setAttribute("open", "");
}
function hideSitePane() {
    elById("site-pane").removeAttribute("open");
}

(() => {
    const openPane = elById("open-pane");
    const sitePane = elById("site-pane");

    const belongsToSitePane = (el) => (
        el === openPane || el === sitePane || sitePane.contains(el)
    );

    // mouse users
    openPane.onmouseover = showSitePane;
    sitePane.onmouseleave = hideSitePane;

    // keyboard users
    sitePane.onfocusin = showSitePane;
    sitePane.onfocusout = hideSitePane;

    // phone users
    openPane.onclick = showSitePane;
    d.onclick = (e) => belongsToSitePane(e.target) || hideSitePane();

    // swipe gestures (for phone users)
    const startPos = {x: null, y: null};
    d.ontouchstart = (e) => {
        // save start pos of touch
        startPos.x = e.touches[0].clientX;
        startPos.y = e.touches[0].clientY;
    };
    d.ontouchmove = (e) => {
        if (startPos.x === null || startPos.y === null) return;
        // calculate difference
        const diffX = startPos.x - e.touches[0].clientX;
        const diffY = startPos.y -  e.touches[0].clientY;

        // early return if just clicked, not swiped
        if (diffX === 0 && diffY === 0) return;

        // reset start pos
        startPos.x = null;
        startPos.y = null;

        let minDiffX = Math.max(
            12,
            0.01 * window.screen.width,
            diffY * 1.5,
        );

        console.debug({diffX, minDiffX});

        if (Math.abs(diffX) >= minDiffX)
            diffX > 0 ? showSitePane() : hideSitePane();
    };
})()
// @license-end
