// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
// stolen from: https://github.com/asozialesnetzwerk/Hangman-Solver/blob/ba693776f634e682553ac37a45157cd0ceeab6a9/js/index.js

import { PopStateHandlers, setMultipleURLParams } from "@utils/utils.js";

const wildCardChar = "_";
// to replace "_" with regex
const wildCardRegex = /_+/g;
// to replace ?, or # with _
const notRealWildCardRegex = /[#?]/g;
// to remove whitespaces
const whiteSpaceRegex = /\s+/g;
// to remove duplicate chars:
const duplicateCharsRegex = /(.)(?=.*\1)/g;

function getForm() {
    return document.getElementById("hangman-solver-form") as HTMLFormElement;
}

interface StringValueObject {
    value: string;
}

const _getLowerCaseValueWithoutWhitespace: (
    input: StringValueObject,
) => string = (input) => input.value.toLowerCase().replace(whiteSpaceRegex, "");

function getHtmlInputElements() {
    return {
        input: [
            // eslint-disable-next-line @typescript-eslint/non-nullable-type-assertion-style
            document.querySelector("input[name='input']") as HTMLInputElement,
            (input: HTMLInputElement) =>
                _getLowerCaseValueWithoutWhitespace(input).replace(
                    notRealWildCardRegex,
                    wildCardChar,
                ),
        ],
        invalid: [
            // eslint-disable-next-line @typescript-eslint/non-nullable-type-assertion-style
            document.querySelector("input[name='invalid']") as HTMLInputElement,
            (input: HTMLInputElement) => {
                // remove invalid chars and normalize
                const value: string = _getLowerCaseValueWithoutWhitespace(input)
                    .replace(
                        notRealWildCardRegex,
                        "",
                    )
                    .replace(wildCardRegex, "");
                // remove duplicates
                const arr: string[] = [
                    ...new Set(value),
                ];
                // sort
                arr.sort();
                return arr.join("");
            },
        ],
        max_words: [
            // eslint-disable-next-line @typescript-eslint/non-nullable-type-assertion-style
            document.querySelector(
                "input[name='max_words']",
            ) as HTMLInputElement,
            (input: StringValueObject): number =>
                Number.parseInt(input.value, 10),
        ],
        crossword_mode: [
            // eslint-disable-next-line @typescript-eslint/non-nullable-type-assertion-style
            document.querySelector(
                "input[name='crossword_mode']",
            ) as HTMLInputElement,
            (input: { checked: boolean }): boolean => input.checked,
        ],
        lang: [
            // eslint-disable-next-line @typescript-eslint/non-nullable-type-assertion-style
            document.querySelector("select[name='lang']") as HTMLSelectElement,
            _getLowerCaseValueWithoutWhitespace,
        ],
    } as const;
}
type HtmlInputElements = ReturnType<typeof getHtmlInputElements>;
type State = {
    [TKey in keyof HtmlInputElements]: ReturnType<HtmlInputElements[TKey][1]>;
};

function getState(): State {
    const inputElements: HtmlInputElements = getHtmlInputElements();
    return {
        input: inputElements.input[1](inputElements.input[0]),
        invalid: inputElements.invalid[1](inputElements.invalid[0]),
        max_words: inputElements.max_words[1](inputElements.max_words[0]),
        crossword_mode: inputElements.crossword_mode[1](
            inputElements.crossword_mode[0],
        ),
        lang: inputElements.lang[1](inputElements.lang[0]),
    };
}

function getHtmlOutputElements() {
    return {
        letterOutput: document.getElementById(
            "letter-frequency-information",
        ) as HTMLDivElement,
        wordOutput: document.getElementById("matching-words") as HTMLDivElement,
    };
}

function getInvalidChars(state: State) {
    return ((state.crossword_mode
        ? ""
        : state.input.replace(wildCardRegex, "")) + state.invalid)
        .toLowerCase()
        .replace(whiteSpaceRegex, "")
        .replace(duplicateCharsRegex, "");
}

function getRegex(state: State) {
    const invalidChars = "[^" + getInvalidChars(state) + "]";
    const regexStr = state.input.replace(wildCardRegex, (s) => {
        return invalidChars + (s.length > 1 ? `{${s.length}}` : "");
    });
    return new RegExp("^" + regexStr + "$", "u");
}

async function loadWords(state: State): Promise<string[]> {
    // eslint-disable-next-line @typescript-eslint/no-misused-spread
    const wordLength = [...state.input].length;
    try {
        return await _loadWords(state.lang, wordLength);
    } catch (e) {
        console.error("error loading words", e);
        return [];
    }
}

const _wordsCache = new Map<string, Map<number, string[]>>();
export async function _loadWords(
    language: string,
    wordLength: number,
): Promise<string[]> {
    let languageCache = _wordsCache.get(language);
    if (languageCache) {
        const words = languageCache.get(wordLength);
        if (words) {
            return words;
        }
    } else {
        languageCache = new Map();
        _wordsCache.set(language, languageCache);
    }
    const response = await fetch(
        `/hangman-loeser/worte/${language.toLowerCase()}/${wordLength}.txt`,
        {
            method: "GET",
            headers: { Accept: "text/plain" },
        },
    );
    if (response.status !== 200 && response.status !== 404) {
        console.error("error loading words", response);
    }
    const words = response.ok ? (await response.text()).split("\n") : [];
    languageCache.set(wordLength, words);
    return words;
}

function updateLettersMap(
    letters: Map<string, number>,
    word: string,
    inputWithoutWildCards: string,
    crossword_mode: boolean,
) {
    if (crossword_mode) {
        for (const char of inputWithoutWildCards) {
            letters.set(char, (letters.get(char) ?? 0) - 1);
        }
        for (const char of word) {
            letters.set(char, (letters.get(char) ?? 0) + 1);
        }
        return;
    }
    // eslint-disable-next-line @typescript-eslint/no-misused-spread
    const used = [...inputWithoutWildCards];
    for (const char of word) {
        if (used.includes(char)) {
            continue;
        }
        letters.set(char, (letters.get(char) ?? 0) + 1);
        used.push(char);
    }
}

async function solveHangman(
    state: State,
): Promise<[string[], Map<string, number>]> {
    const words = await loadWords(state);
    const invalidChars = state.invalid;

    const inputWithoutWildCards = state.input.replace(wildCardRegex, "");
    const matchesAlways = invalidChars.length === 0 &&
        inputWithoutWildCards.length === 0; // no letter input, only wildcards

    if (inputWithoutWildCards.length === state.input.length) { // max one word, without wildcard, just search for it
        const word = inputWithoutWildCards.toLowerCase();
        if (binarySearch(words, word)) { // if the word is present
            return [[word], new Map<string, number>()];
        }
        return [[], new Map<string, number>()];
    } else if (matchesAlways) {
        const letters = new Map<string, number>();
        words.forEach((word) => {
            updateLettersMap(letters, word, "", state.crossword_mode);
        });
        return [words, letters];
    } else { // have to search
        const letters = new Map<string, number>();
        const regex = getRegex(state);
        return [
            words.filter((word) => {
                if (regex.test(word)) {
                    updateLettersMap(
                        letters,
                        word,
                        inputWithoutWildCards,
                        state.crossword_mode,
                    );
                    return true;
                }
                return false;
            }),
            letters,
        ];
    }
}

async function onStateChange(state: State) {
    console.debug("state changed", state);
    const [foundWords, letters] = await solveHangman(state);

    const outputs = getHtmlOutputElements();
    if (foundWords.length > 0) {
        outputs.wordOutput.replaceChildren(
            Math.min(state.max_words, foundWords.length).toString(),
            "/",
            foundWords.length.toString(),
            " passenden Wörter:",
            <ul>
                {foundWords.slice(0, state.max_words).map((word) => (
                    <li>{[word]}</li>
                ))}
            </ul>,
        );

        const lettersSorted: [string, number][] = [...letters.entries()].filter(
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            ([_, count]) => count > 0,
        );
        lettersSorted.sort((a, b) => b[1] - a[1]);
        outputs.letterOutput.replaceChildren(
            "Mögliche Buchstaben: ",
            lettersSorted
                .map((value) => value.join(": "))
                .join(", "),
        );
    } else {
        outputs.letterOutput.replaceChildren("Nichts gefunden.");
        outputs.wordOutput.replaceChildren("");
    }
}

function binarySearch<T>(arr: T[], toSearch: T): boolean {
    let start = 0;
    let end = arr.length - 1;
    // Iterate while start not meets end
    while (start <= end) {
        // Find the mid-index
        const mid = Math.floor((start + end) / 2);
        // If element is present at mid, return True
        if (arr[mid] === toSearch) {
            return true;
        } // Else look in left or right half accordingly
        else if (arr[mid]! < toSearch) {
            start = mid + 1;
        } else {
            end = mid - 1;
        }
    }
    return false;
}

const stateType = "HangmanSolverState";
function updateCurrentState(event: Event | undefined = undefined) {
    const newState = getState();
    setMultipleURLParams(
        Object.entries(newState).map(([key, value]) => [key, value.toString()]),
        newState,
        stateType,
    );
    event?.preventDefault();
    return onStateChange(newState);
}

function populateFormFromState(state: State) {
    const inputElements = getHtmlInputElements();
    inputElements.input[0].value = state.input;
    inputElements.crossword_mode[0].checked = state.crossword_mode;
    inputElements.invalid[0].value = state.invalid;
    inputElements.max_words[0].value = state.max_words.toString();
    inputElements.lang[0].value = state.lang;
}

function loadFromState(event: PopStateEvent) {
    const state = event.state as State;
    populateFormFromState(state);
    event.preventDefault();
    return onStateChange(state);
}

function addEventListeners() {
    PopStateHandlers[stateType] = loadFromState;
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    getForm().addEventListener("submit", updateCurrentState);
    const inputElements = getHtmlInputElements();
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    inputElements.lang[0].addEventListener("change", updateCurrentState);
    inputElements.crossword_mode[0].addEventListener(
        "change",
        // eslint-disable-next-line @typescript-eslint/no-misused-promises
        updateCurrentState,
    );
}

addEventListeners();
