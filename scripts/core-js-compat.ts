#!/usr/bin/env -S deno run --unstable --allow-env --allow-read
import compat from "npm:core-js-compat@3.28.0";

const {
    list,
    targets,
} = compat({
    targets: "defaults",
    version: "3.28",
    inverse: false,
});

console.log(targets);
