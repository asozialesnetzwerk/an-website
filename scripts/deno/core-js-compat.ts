#!/usr/bin/env -S deno run --no-prompt --allow-read=.
import compat from "npm:core-js-compat@3";
import { parse } from "std/flags/mod.ts";

const args = parse(Deno.args, {
    boolean: "inverse",
    string: ["targets", "version"],
    default: {
        targets: ">=0.1% and supports es6-module,Chrome>=120,Firefox>=115,Safari>=15.6",
    },
});

const {
    list,
    targets,
    // @ts-expect-error TS2379
} = compat({
    modules: "core-js/stable",
    targets: args.targets,
    version: args.version,
    inverse: args.inverse,
});

console.log(targets);
console.log(list.length);
