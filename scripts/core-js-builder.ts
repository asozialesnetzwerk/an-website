#!/usr/bin/env -S node --loader=ts-node/esm
import builder from "core-js-builder";
import { gzipSize } from "gzip-size";
import { transform } from "esbuild";
import { parseArgs } from "@std/cli/parse-args";

const args = parseArgs(process.argv.slice(2), {
    string: ["targets", "format"],
    default: {
        targets:
            ">=0.1% and supports es6-module-dynamic-import, Chrome 138, Firefox 140, Safari 18.5, iOS 18.5",
        format: "bundle",
    },
});

const output = await builder({
    modules: "core-js/stable",
    targets: args.targets,
    summary: {
        console: { size: args.format === "bundle", modules: false },
        comment: { size: false, modules: args.format === "bundle" },
    },
    format: args.format as ("bundle" | "esm" | "cjs"),
    filename: args._[0] as string,
});

if (args.format === "bundle") {
    const minified = (await transform(output, { minify: true })).code;
    console.log(
        "Minified size:",
        minified.length,
        "bytes uncompressed,",
        await gzipSize(minified),
        "bytes gzipped.",
    );
}
