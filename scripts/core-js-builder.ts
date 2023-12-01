#!/usr/bin/env -S deno run --allow-env --allow-read --allow-write
import builder from "npm:core-js-builder@3.30.1";
import { modules } from "./core-js-modules.ts";
import { gzipSizeSync } from "npm:gzip-size";

const bundle = await builder({
    targets: "defaults",
    modules: modules,
    summary: {
        console: { size: true, modules: false },
        comment: { size: false, modules: true },
    },
    format: "bundle",
    filename: Deno.args[0],
});

console.log("Gzip size:", gzipSizeSync(bundle), "bytes");
