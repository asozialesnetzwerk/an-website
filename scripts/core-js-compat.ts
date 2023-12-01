#!/usr/bin/env -S deno run --unstable --allow-env --allow-read
import { parse } from "https://deno.land/std@0.177.0/flags/mod.ts";
import compat from "npm:core-js-compat@3";

const args = parse(Deno.args, {
    boolean: "inverse",
    string: ["targets", "version"],
    default: { targets: "defaults" },
});

const {
    list,
    targets,
} = compat({
    targets: args.targets,
    version: args.version,
    inverse: args.inverse,
});

console.log(targets);
