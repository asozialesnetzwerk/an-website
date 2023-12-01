#!/usr/bin/env -S deno run --allow-env --allow-read --allow-write
import builder from "npm:core-js-builder@3";
import modules from "./core-js-modules.ts";
import { gzipSize } from "npm:gzip-size";
import { parse } from "std/flags/mod.ts";

const args = parse(Deno.args, {
    string: ["targets", "format"],
    default: { targets: "defaults", format: "bundle" },
});

const bundle = await builder({
    targets: args.targets,
    modules: modules,
    summary: {
        console: { size: args.format === "bundle", modules: false },
        comment: { size: false, modules: args.format === "bundle" },
    },
    format: args.format,
    filename: args._[0],
});

if (args.format === "bundle") {
    console.log("Gzip size:", await gzipSize(bundle), "bytes");
}
