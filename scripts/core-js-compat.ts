#!/usr/bin/env -S deno run --allow-env --allow-read
import { parse } from "std/flags/mod.ts";
import compat from "npm:core-js-compat@3";
import { modules } from "./core-js-modules.ts";

const args = parse(Deno.args, {
    boolean: "inverse",
    string: ["targets", "version"],
    default: { targets: "defaults" },
});

const {
    list,
    targets,
} = compat({
    modules: modules,
    targets: args.targets,
    version: args.version,
    inverse: args.inverse,
});

console.log(targets);
console.log(list.length);
