#!/usr/bin/env -S pnpm ts-node -T
import compat from "core-js-compat";
import { parseArgs } from "@std/cli/parse-args";

const args = parseArgs(process.argv.slice(2), {
    boolean: "inverse",
    string: ["targets", "version"],
    default: {
        targets:
            ">=0.1% and supports es6-module, Chrome 120, Firefox ESR, Safari 15.6",
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
