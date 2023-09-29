#!/usr/bin/env -S pnpm ts-node -T
import builder from "core-js-builder";
import { transform } from "esbuild";
import { gzipSize } from "gzip-size";
import { parse } from "./vendored/flags.ts";

const args = parse(process.argv.slice(2), {
    string: ["targets", "format"],
    default: {
        targets:
            ">=0.1% and supports es6-module,Chrome>=120,Firefox>=115,Safari>=15.6",
        format: "bundle",
    },
});

const bundle = await builder({
    modules: "core-js/stable",
    targets: args.targets,
    summary: {
        console: { size: args.format === "bundle", modules: false },
        comment: { size: false, modules: args.format === "bundle" },
    },
    format: args.format,
    // @ts-expect-error TS2412
    filename: args._[0],
});

if (args.format === "bundle") {
    const minified = (await transform(bundle, { minify: true })).code;
    console.log(
        "Minified size:",
        minified.length,
        "bytes uncompressed,",
        await gzipSize(minified),
        "bytes gzipped.",
    );
}
