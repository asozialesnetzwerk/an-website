#!/usr/bin/env -S pnpm ts-node -T
import builder from "core-js-builder";
import { transform } from "esbuild";
import { gzipSize } from "gzip-size";
import parse from "minimist";

const args = parse(process.argv.slice(2), {
    string: ["targets", "format"],
    default: {
        targets: ">=0.1% and supports es6-module,Firefox>=115,Chrome>=120",
        format: "bundle",
    },
});

const bundle = await builder({
    modules: "core-js/stable",
    targets: args["targets"] as string,
    summary: {
        console: { size: args["format"] === "bundle", modules: false },
        comment: { size: false, modules: args["format"] === "bundle" },
    },
    // @ts-expect-error TS2322
    format: args["format"] as string,
    filename: args._[0],
});

if (args["format"] === "bundle") {
    const minified = (await transform(bundle, { minify: true })).code;
    console.log(
        "Minified size:",
        minified.length,
        "bytes uncompressed,",
        await gzipSize(minified),
        "bytes gzipped.",
    );
}
