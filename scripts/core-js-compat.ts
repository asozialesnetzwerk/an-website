#!/usr/bin/env -S node --loader=ts-node/esm
import compat from "core-js-compat";
import { parseArgs } from "@std/cli/parse-args";

const args = parseArgs(process.argv.slice(2), {
    boolean: "inverse",
    string: ["targets", "version"],
    default: {
        targets:
            ">=0.1% and supports es6-module-dynamic-import, Chrome 138, Firefox 140, Safari 18.5, iOS 18.5",
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
