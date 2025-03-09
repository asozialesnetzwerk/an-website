// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT
// Source: https://github.com/VanishMax/vanilla-jsx

type Tag = string | ((props: Props, children: Children) => Element);
type Props = Record<string, string | number | null | undefined> | null;
type Children = (Node | string | (Node | string)[])[];

export const h = (tag: Tag, props: Props, ...children: Children) => {
    // If the tag is a function component, pass props and children inside it
    if (typeof tag === 'function') {
        return tag({ ...props }, children);
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
    children.flatMap((child) => Array.isArray(child) ? child : [child]).forEach((child) => {
        el.append(child);
    });

    return el;
};
