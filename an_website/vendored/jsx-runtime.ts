// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
// Source: https://github.com/VanishMax/vanilla-jsx
declare global {
    namespace JSX {
        interface __Props {
            id?: string;
            className?: string;
            tooltip?: string;
        }

        interface IntrinsicElements {
            div: __Props;
            img: __Props & { src?: string, alt?: string };
        }
    }
}

type Component = (props: Props, children: Children) => HTMLElement;
type Tag = (keyof JSX.IntrinsicElements) | Component;
type Props = Record<string, string | number | null | undefined> | null;
type Children = (Node | string)[];

export const jsx = <T extends Tag>(
    tag: T,
    props: Props,
    ...children: Children
): T extends Component ? ReturnType<T> : HTMLElement => {
    console.debug("jsx", { tag, props, children });
    // If the tag is a function component, pass props and children inside it
    if (typeof tag === 'function') {
        return tag({ ...props }, children) as (T extends Component ? ReturnType<T> : HTMLElement);
    }

    // Create the element and add attributes to it
    const el = document.createElement(tag);
    if (props) {
        Object.entries(props).forEach(([key, val]) => {
            if (key === 'className') {
                el.classList.add(...(val as string || '').trim().split(' '));
                return;
            }

            el.setAttribute(key, val as string);
        });
    }

    // Append all children to the element
    for (const child of children) {
        el.append(child);
    }

    return el as (T extends Component ? ReturnType<T> : HTMLElement);
};

export const jsxs = <T extends Tag>(
    tag: T,
    props: Props & { children: Children },
): T extends Component ? ReturnType<T> : HTMLElement => {
    console.debug("jsxs", { tag, props: { ...props } });
    const children = props.children;
    const properties: Props = props;
    delete properties["children"];
    return jsx(tag, properties, ...children);
};
