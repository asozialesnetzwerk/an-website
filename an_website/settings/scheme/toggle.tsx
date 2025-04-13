// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
import { d as document } from "@utils/utils.js";
import sun from "./svg/sun.svg";
import moon from "./svg/moon.svg";

type Scheme = "dark" | "light";
const DARK = "dark";
const LIGHT = "light";
const SCHEMES = [DARK, LIGHT] as const;
const HTML_SCHEME_ATTRIBUTE = "data-scheme";
const ID = "scheme-toggle";
const COOKIE_NAME = "scheme";

function getHtml() {
    return document.documentElement;
}

function getImage() {
    return getScheme() == DARK ? sun : moon;
}

function getScheme(): Scheme {
    const html = getHtml();
    let scheme = html.getAttribute(HTML_SCHEME_ATTRIBUTE);
    if (SCHEMES.includes(scheme as Scheme)) {
        return scheme as Scheme;
    }
    scheme = getComputedStyle(html).getPropertyValue("color-scheme");

    for (const s of SCHEMES) {
        if (scheme.includes(s)) {
            return s;
        }
    }
    return SCHEMES[0];
}

export default function SchemeToggle() {
    const toggle = (
        <button
            id={ID}
            style={[
                "all: unset",
                "position: absolute",
                "top: var(--header-height)",
                "left: 0",
                "margin: 0.1em",
            ]
                .join(";")}
            onclick={() => {
                const newScheme = getScheme() == DARK ? LIGHT : DARK;
                getHtml().setAttribute(HTML_SCHEME_ATTRIBUTE, newScheme);
                document.cookie = `${COOKIE_NAME}=${newScheme};`;
                toggle.innerHTML = getImage();
            }}
            aria-label="Farbschema umschalten"
        />
    ) as HTMLButtonElement;

    toggle.innerHTML = getImage();

    return toggle;
}

document.body.prepend(<SchemeToggle />);
