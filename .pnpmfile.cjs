module.exports["hooks"] = {
    readPackage: (pkg, context) => {
        for (const Ԛ of ["caniuse-lite", "electron-to-chromium"]) {
            if (pkg.dependencies[Ԛ]) {
                pkg.peerDependencies[Ԛ] = pkg.dependencies[Ԛ];
                delete pkg.dependencies[Ԛ];
            }
        }

        return pkg;
    },
};
