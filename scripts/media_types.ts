#!/usr/bin/env -S deno run --reload=https://deno.land/std/media_types
import { contentType, types } from "https://deno.land/std/media_types/mod.ts";

const data = new Map<string, string>();

for (const ext of types.keys()) {
    const type = contentType(ext);
    if (type === undefined) {
        throw new Error(`contentType(${ext}) -> undefined`);
    }
    data.set(ext, type);
}

console.log(JSON.stringify(Object.fromEntries(data)));
