// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
declare global {
    namespace JSX {
        interface __Props {
            id?: string;
            className?: string;
            tooltip?: string;
            children?: (Node | string)[];
        }

        interface IntrinsicElements {
            div: __Props;
            img: __Props & { src?: string, alt?: string };
        }

        type Element = HTMLElement | string;
    }
}

type Component = (props: Props, key?: string) => JSX.Element;
type Tag = (keyof JSX.IntrinsicElements) | Component;
type Props = Record<string, string | number | null | undefined | EventListener | EventListenerObject> & { children?: Children };
type Children = (Node | string)[];

export const jsx = (
    tag: Tag,
    props: Props,
    key?: string,
    log = true,
): JSX.Element => {
    if (log) {
        console.debug("jsx", { tag, props, key });
    }
    // If the tag is a function component, pass props and children inside it
    if (typeof tag === "function") {
        return tag(props);
    }

    // Create the element and add attributes to it
    const el = document.createElement(tag);

    Object.entries(props).forEach(([key, val]) => {
        if (key === "children") {
            // Append all children to the element
            (val as Children | undefined)?.forEach((child) => {
                el.append(child);
            });
        } else if (key === "className") {
            el.className = val as string;
        } else if (key.startsWith("on")) {
            el.addEventListener(key.slice(2)!, val as (EventListener | EventListenerObject));
        } else {
            el.setAttribute(key, val as string);
        }
    });

    console.debug("rendered", el);

    return el;
};

export const jsxs = (
    tag: Tag,
    props: Props & { children: Children },
    key?: string,
): JSX.Element => {
    console.debug("jsxs", { tag, props, key });
    return jsx(tag, props, key, false);
}
