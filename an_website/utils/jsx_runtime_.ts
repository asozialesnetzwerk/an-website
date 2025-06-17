// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
import { d } from "./utils.js";
declare global {
    // eslint-disable-next-line @typescript-eslint/no-namespace
    namespace JSX {
        interface __CanHaveChildren {
            children?: (Node | string)[];
        }
        interface ___Props {
            "id"?: string;
            "className"?: string;
            "tooltip"?: string;
            "style"?: string;
            "aria-label"?: string;
        }

        type __Events = {
            [Prop in keyof HTMLElementEventMap as `on${Prop}`]?:
                | undefined
                | ((event: HTMLElementEventMap[Prop]) => void);
        };

        type __Props = ___Props & __Events;

        interface IntrinsicElements {
            div: __CanHaveChildren & __Props;
            img: __CanHaveChildren & __Props & { src?: string; alt?: string };
            ul: __CanHaveChildren & __Props;
            li: __CanHaveChildren & __Props;
            a: __CanHaveChildren & __Props & { href?: string };
            p: __CanHaveChildren & __Props;
            button: __CanHaveChildren & __Props & { title?: string };
            span: __CanHaveChildren & __Props;
            input: __Props & {
                type: string;
                min?: string;
                max?: string;
                value?: string;
            };
            style: __CanHaveChildren;
        }

        type Element = Node | string;
    }
}

type Component = (props: Props, key?: string) => JSX.Element;
type Tag = (keyof JSX.IntrinsicElements) | Component;
type Props =
    & Record<
        string,
        string | number | null | undefined | EventListener | EventListenerObject
    >
    & { children?: Children };
type Children = (Node | string)[];

const children = "children";
const className = "className";

const appendChildren = (element: ParentNode, children?: Children): void => {
    children?.forEach((child) => {
        element.append(child);
    });
};

export const jsx = (
    tag: Tag,
    props: Props,
): JSX.Element => {
    console.debug("jsx", { tag, props });

    // If the tag is a function component, pass props and children inside it
    if (typeof tag === "function") {
        return tag(props);
    }

    // Create the element and add attributes to it
    const el = d.createElement(tag);

    Object.entries(props).forEach(([key, val]) => {
        if (key === children) {
            // Append all children to the element
            appendChildren(el, val as Children | undefined);
        } else if (key === className) {
            el[className] = val as string;
        } else if (key.startsWith("on")) {
            if (val) {
                el.addEventListener(
                    key.slice(2),
                    val as (EventListener | EventListenerObject),
                );
            }
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
): JSX.Element => {
    console.debug("jsxs", { tag, props });
    return jsx(tag, props);
};

export const Fragment = (
    props: { children?: Children },
): JSX.Element => {
    console.debug("Fragment", props);
    const frag = new DocumentFragment();
    appendChildren(frag, props[children]);
    return frag;
};
