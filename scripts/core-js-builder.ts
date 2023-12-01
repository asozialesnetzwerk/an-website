#!/usr/bin/env -S deno run --unstable --allow-env --allow-read --allow-write
import builder from "npm:core-js-builder@3.28.0";

await builder({
    targets: "defaults",
    summary: {
        console: { size: true, modules: false },
        comment: { size: false, modules: true },
    },
    format: "bundle",
    filename: Deno.args[0],
});
