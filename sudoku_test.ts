// deno-fmt-ignore-file

import { assertEquals } from "std/assert/mod.ts";
import { sudoku, _ } from "./sudoku.ts";

Deno.test(String(_), () => {
    assertEquals(undefined, sudoku(
        7, 9, 2,  3, 5, 4,  6, 1, 8,
        8, 5, 4,  1, 2, 6,  3, 9, 7,
        3, 6, 1,  9, 8, 7,  5, 2, 4,

        9, 4, 5,  6, 3, 8,  1, 7, 2,
        2, 7, 8,  5, 4, 1,  9, 3, 6,
        6, 1, 3,  7, 9, 2,  8, 4, 5,

        4, 2, 9,  8, 1, 5,  7, 6, 3,
        1, 8, 7,  2, 6, 3,  4, 5, 9,
        5, 3, 6,  4, 7, 9,  2, 8, 1,
    ));
});
