// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later

// these functions break if used the css-only functionality of the site-pane
function showSitePane() {
    elById("site-pane").style.right = "0";
}
function hideSitePane() {
    elById("site-pane").style.right = "-70%";
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
        // reset start pos
        startPos.x = null;
        startPos.y = null;
        // early return if just clicked, not swiped
        if (diffX === 0 && diffY === 0) return;

        if (Math.abs(diffX) > Math.abs(diffY)) {
            // sliding horizontally
            if (diffX > 0) {
                showSitePane();
            } else {
                hideSitePane();
            }
            e.preventDefault();
        }
    };
})()
// @license-end
