#!/usr/bin/env -S pnpm ts-node -T
import compat from "core-js-compat";
import parse from "minimist";

const args = parse(process.argv.slice(2), {
    boolean: "inverse",
    string: ["targets", "version"],
    default: {
        targets: ">=0.1% and supports es6-module,Firefox>=115,Chrome>=120",
    },
});

const {
    list,
    targets,
    // @ts-expect-error TS2379
} = compat({
    modules: "core-js/stable",
    targets: args["targets"] as string,
    version: args["version"] as string | undefined,
    inverse: args["inverse"] as boolean,
});

console.log(targets);
console.log(list.length);
