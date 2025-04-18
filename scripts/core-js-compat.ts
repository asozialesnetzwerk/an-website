#!/usr/bin/env -S node --loader=ts-node/esm
import compat from "core-js-compat";
import { parseArgs } from "@std/cli/parse-args";

const args = parseArgs(process.argv.slice(2), {
    boolean: "inverse",
    string: ["targets", "version"],
    default: {
        targets:
            ">=0.1% and supports es6-module-dynamic-import, Chrome 120, Firefox 115, Safari 15.6",
    },
});

const {
    list,
    targets,
} = compat({
    modules: "core-js/stable",
    targets: args.targets,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    version: args.version!,
    inverse: args.inverse,
});

console.log(targets);
console.log(list.length);
