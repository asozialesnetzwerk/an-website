// @ts-check

/** @import { PackageManifest } from "@pnpm/types" */

/**
 * @template T
 * @param {T} thing
 * @returns {NonNullable<T>}
 */
function assertNonNullable(thing) {
    return /** @type {NonNullable<T>} */ (thing);
}

// eslint-disable-next-line no-undef
module.exports.hooks = {
    /**
     * @param {PackageManifest} pkg
     * @param {unknown} context
     */
    // @ts-expect-error TS6133
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    readPackage: (pkg, context) => {
        for (
            const Ԛ of ["@types/node", "caniuse-lite", "electron-to-chromium"]
        ) {
            const dependencies = assertNonNullable(pkg.dependencies);
            const peerDependencies = assertNonNullable(pkg.peerDependencies);
            if (dependencies[Ԛ]) {
                peerDependencies[Ԛ] = dependencies[Ԛ];
                // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
                delete dependencies[Ԛ];
            }
        }
        return pkg;
    },
};
