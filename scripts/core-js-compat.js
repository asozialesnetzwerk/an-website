#!/usr/bin/env -S node
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
} = compat({
    modules: "core-js/stable",
    targets: args["targets"],
    version: args["version"],
    inverse: args["inverse"],
});

console.log(targets);
console.log(list.length);
