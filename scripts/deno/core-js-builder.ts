#!/usr/bin/env -S deno run --node-modules-dir --no-prompt --allow-net=deno.land --allow-env=TMPDIR,TMP,TEMP --allow-read=.,/tmp --allow-write=.,/tmp
import builder from "npm:core-js-builder@3";
import * as esbuild from "esbuild/wasm.js";
import { parseArgs } from "std/cli/mod.ts";
import { gzipSize } from "npm:gzip-size";

const args = parseArgs(Deno.args, {
    string: ["targets", "format"],
    default: {
        targets:
            ">=0.1% and supports es6-module, Chrome 120, Firefox ESR, Safari 15.6",
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
    const minified = (await esbuild.transform(bundle, { minify: true })).code;
    console.log(
        "Minified size:",
        minified.length,
        "bytes uncompressed,",
        await gzipSize(minified),
        "bytes gzipped.",
    );
}

esbuild.stop();
