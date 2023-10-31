// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
export {};

function startLoadingComics() {
    const getDateBy = (year: number, month: number, dayOfMonth: number): Date =>
        new Date(year, month - 1, dayOfMonth, 6, 0, 0, 0);
    // date with special link format
    const wrongLinks: [Date, string][] = [
        [
            getDateBy(2021, 5, 25),
            "administratives/kaenguru-comics/25/original/",
        ],
        [
            getDateBy(2021, 9, 6),
            "administratives/kaenguru-comics/2021-09/6/original/",
        ],
        [
            getDateBy(2021, 10, 4),
            "administratives/kaenguru-comics/2021-10/4/original",
        ],
        [
            getDateBy(2021, 10, 29),
            "administratives/kaenguru-comics/29/original",
        ],
        [
            getDateBy(2021, 11, 3),
            "administratives/kaenguru-comics/2021-11/03-11-21/original",
        ],
        [
            getDateBy(2021, 12, 6),
            "administratives/kaenguru-comics/2021-12/6/original",
        ],
        [
            getDateBy(2022, 1, 29),
            "administratives/kaenguru-comics/2022-01/29-3/original",
        ],
        [
            getDateBy(2022, 2, 7),
            "administratives/kaenguru-comics/08-02-22/original",
        ],
        [
            getDateBy(2022, 2, 12),
            "administratives/kaenguru-comics/12/original",
        ],
        [
            getDateBy(2022, 2, 14),
            "administratives/kaenguru-comics/14/original",
        ],
        [
            getDateBy(2022, 3, 28),
            "administratives/kaenguru-comics/2022-03/kaenguru-2022-03-28/original",
        ],
        [
            getDateBy(2022, 4, 4),
            "administratives/kaenguru-comics/2022-04/4/original",
        ],
        [
            getDateBy(2022, 5, 9),
            "administratives/kaenguru-comics/2022-05/9/original",
        ],
        [
            getDateBy(2022, 8, 15),
            "administratives/kaenguru-comics/2022-08/kaenguru-comics-2022-08-15/original",
        ],
        [
            getDateBy(2022, 8, 29),
            "administratives/kaenguru-comics/2022-08/29-3/original",
        ],
    ];

    const dateEquals = (
        date: Date,
        year: number,
        month: number,
        dayOfMonth: number,
    ): boolean => (
        // check if a date equals another based on year, month, and dayOfMonth
        date.getFullYear() === year &&
        date.getMonth() === (month - 1) && // JS is stupid
        date.getDate() === dayOfMonth
    );

    const datesEqual = (date1: Date, date2: Date): boolean =>
        dateEquals(
            date1,
            date2.getFullYear(),
            date2.getMonth() + 1, // JS is stupid
            date2.getDate(),
        );

    const isSunday = (date: Date | undefined) => (
        date &&
        date.getDay() === 0 &&
        // exception for 2020-12-20 (sunday) because there was a comic
        !dateEquals(date, 2020, 12, 20)
    );

    const copyDate = (date: Date): Date =>
        getDateBy(date.getFullYear(), date.getMonth() + 1, date.getDate());

    // get today without hours, minutes, seconds and ms
    const getToday = (): Date => copyDate(new Date());

    const comics: string[] = [];

    const links = `/static/img/2020-11-03.jpg
administratives/kaenguru-comics/pilot-kaenguru/original
administratives/kaenguru-comics/pow-kaenguru/original
static/img/kaenguru-announcement/original
administratives/kaenguru-comics/der-baum-kaenguru/original
administratives/kaenguru-comics/warnung-kaenguru/original
administratives/kaenguru-comics/kaenguru-005/original
administratives/kaenguru-comics/kaenguru-006/original
administratives/kaenguru-comics/kaenguru-007/original
administratives/kaenguru-comics/kaenguru-008/original
administratives/kaenguru-comics/kaenguru-009/original
administratives/kaenguru-comics/kaenguru-010/original
administratives/kaenguru-comics/kaenguru-011/original
administratives/kaenguru-comics/kaenguru-012/original
administratives/kaenguru-comics/kaenguru-013/original
administratives/kaenguru-comics/kaenguru-014/original
administratives/kaenguru-comics/kaenguru-015/original
administratives/kaenguru-comics/kaenguru-016/original
administratives/kaenguru-comics/kaenguru-017/original
administratives/kaenguru-comics/kaenguru-018/original
administratives/2020-12/kaenguru-comics-kaenguru-019/original
administratives/kaenguru-comics/kaenguru-020/original
administratives/kaenguru-comics/kaenguru-021/original
administratives/kaenguru-comics/kaenguru-023/original
administratives/kaenguru-comics/kaenguru-024/original
administratives/kaenguru-comics/kaenguru-025/original
administratives/kaenguru-comics/kaenguru-026/original
administratives/kaenguru-comics/kaenguru-027/original
administratives/kaenguru-comics/kaenguru-028/original
administratives/kaenguru-comics/kaenguru-029/original
administratives/kaenguru-comics/kaenguru-030/original
administratives/kaenguru-comics/kaenguru-031/original
administratives/kaenguru-comics/kaenguru-032/original
administratives/kaenguru-comics/kaenguru-033/original
administratives/kaenguru-comics/kaenguru-034/original
administratives/kaenguru-comics/kaenguru-035/original
administratives/kaenguru-comics/kaenguru-036/original
administratives/kaenguru-comics/kaenguru-037/original
administratives/kaenguru-comics/kaenguru-038-2/original
administratives/kaenguru-comics/kaenguru-039/original
administratives/kaenguru-comics/kaenguru-040/original
administratives/kaenguru-comics/kaenguru-41/original
administratives/kaenguru-comics/kaenguru-42/original
administratives/kaenguru-comics/kaenguru-43/original
administratives/kaenguru-comics/kaenguru-44/original
administratives/kaenguru-comics/kaenguru-045/original
`;
    function addLinksToComics(): void {
        const today = getToday();
        const date = copyDate(firstDateWithNewLink);
        while (date.getTime() <= today.getTime()) {
            comics.push(generateComicLink(date));
            dateIncreaseByDays(date, 1);
        }
    }

    const days: [string, string, string, string, string, string, string] = [
        "Sonntag",
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
    ];
    // @ts-expect-error TS2322
    const getDayName = (date: Date): string => days[date.getDay()];
    const months: [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
    ] = [
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ];
    // @ts-expect-error TS2322
    const getMonthName = (date: Date): string => months[date.getMonth()];

    const getDateString = (date: Date): string => (
        `Comic von ${getDayName(date)}, dem ${date.getDate()}. ${
            getMonthName(date)
        } ${date.getFullYear()}`
    );

    function removeAllPopups() {
        for (const node of document.getElementsByClassName("popup-container")) {
            node.remove();
        }
    }

    const currentImgHeader = document.getElementById(
        "current-comic-header",
    ) as HTMLAnchorElement;
    const currentImg = document.getElementById(
        "current-img",
    ) as HTMLImageElement;
    currentImg.onmouseover = removeAllPopups;
    // const currentImgContainer = document.getElementById("current-img-container");
    function setCurrentComic(date: Date) {
        let link = generateComicLink(date);
        link = link.startsWith("/") ? link : "https://img.zeit.de/" + link;
        currentImg.src = link;
        // currentImg.crossOrigin = "";
        currentImgHeader.innerText = "Neuster " + getDateString(date) + ":";
        currentImgHeader.href = link;
    }

    const firstDateWithOldLink = getDateBy(2020, 12, 3);
    const oldLinkRegex =
        /administratives\/kaenguru-comics\/kaenguru-(\d{2,3})(?:-2)?\/original\/?/;

    const firstDateWithNewLink = getDateBy(2021, 1, 19);
    const newLinkRegex =
        /administratives\/kaenguru-comics\/(\d{4})-(\d{2})\/(\d{2})\/original\/?/;

    const relativeLinkRegex = /\/static\/img\/(\d{4})-(\d{1,2})-(\d{1,2})\.jpg/;

    function getDateFromLink(link: string): Date | null {
        for (const reg of [newLinkRegex, relativeLinkRegex]) {
            // URLs with year, month, day in them as three groups
            const match = link.toLowerCase().match(reg);
            if (match && match.length > 3) {
                return getDateBy(
                    // @ts-expect-error TS2345
                    parseInt(match[1]),
                    // @ts-expect-error TS2345
                    parseInt(match[2]),
                    // @ts-expect-error TS2345
                    parseInt(match[3]),
                );
            }
        }
        // URLs with incrementing number in them
        const arr = link.toLowerCase().match(oldLinkRegex);
        if (arr && arr.length > 1) {
            // @ts-expect-error TS2345
            const num = parseInt(arr[1]) - 5;
            const date = new Date(firstDateWithOldLink.getTime());
            for (let i = 0; i < num; i++) {
                date.setTime(
                    dateIncreaseByDays(date, isSunday(date) ? 2 : 1).getTime(),
                );
            }
            return isSunday(date) ? dateIncreaseByDays(date, 1) : date;
        }
        link = link.toLowerCase().trim();
        switch (link) { // first URLs with special format
            case "administratives/kaenguru-comics/pilot-kaenguru/original":
                return getDateBy(2020, 11, 29);
            case "administratives/kaenguru-comics/pow-kaenguru/original":
                return getDateBy(2020, 11, 30);
            case "static/img/kaenguru-announcement/original":
                return getDateBy(2020, 11, 30);
            case "administratives/kaenguru-comics/der-baum-kaenguru/original":
                return getDateBy(2020, 12, 1);
            case "administratives/kaenguru-comics/warnung-kaenguru/original":
                return getDateBy(2020, 12, 2);
            case "administratives/2020-12/kaenguru-comics-kaenguru-019/original":
                return getDateBy(2020, 12, 19);
        }
        for (const arr of wrongLinks) {
            if (link === arr[1]) {
                return arr[0];
            }
        }
        return null;
    }

    const linkFormat = "administratives/kaenguru-comics/%y-%m/%d/original";

    function generateComicLink(date: Date): string {
        for (const arr of wrongLinks) {
            if (datesEqual(date, arr[0])) {
                return arr[1];
            }
        }
        const month = (date.getMonth() + 1).toString();
        const day = date.getDate().toString();
        return linkFormat
            .replace("%y", date.getFullYear().toString())
            .replace("%m", month.length === 2 ? month : "0" + month)
            .replace("%d", day.length === 2 ? day : "0" + day);
    }

    function dateIncreaseByDays(date: Date, days: number): Date {
        date.setTime(
            // working in milliseconds
            date.getTime() + (days * 1000 * 60 * 60 * 24),
        );
        date.setHours(6); // to compensate errors through daylight savings time
        return date;
    }

    const comicCountToLoadOnCLick = 7;
    const loadButton = document.getElementById("load-button")!;
    const list = document.getElementById("old-comics-list")!;
    let loaded = 0;

    const loadMoreComics = () => {
        for (let i = 0; i < comicCountToLoadOnCLick; i++) {
            loaded++;
            const c = comics.length - loaded;
            if (c < 0) {
                break;
            }

            let link = comics[c];
            // @ts-expect-error TS2345
            const date = getDateFromLink(link);
            if (date === null) {
                console.error("No date found for " + link);
                continue;
            }
            // @ts-expect-error TS2532
            link = link.startsWith("/") ? link : "https://img.zeit.de/" + link;

            const listItem = document.createElement("li");
            const header = document.createElement("a");
            header.classList.add("comic-header");
            header.innerText = getDateString(date) + ":";
            // @ts-expect-error TS2322
            header.href = link;
            header.style.fontSize = "25px";
            listItem.appendChild(header);
            listItem.appendChild(document.createElement("br"));
            const image = document.createElement("img");
            image.classList.add("normal-img");
            // image.crossOrigin = "";
            // @ts-expect-error TS2322
            image.src = link;
            image.alt = getDateString(date);
            image.onclick = () => {
                createImgPopup(image);
            };
            image.onerror = () => {
                if (isSunday(date)) {
                    // normally the image is not available on sundays
                    // so we can remove the image if it is not available
                    list.removeChild(listItem);
                } else {
                    // if the image is not available, display an error message
                    listItem.append(" konnte nicht geladen werden.");
                }
            };
            listItem.appendChild(image);
            list.appendChild(listItem);
        }

        if (loaded >= comics.length) {
            loadButton.style.opacity = "0";
            loadButton.style.visibility = "invisible";
        }
    };
    (document.getElementById("load-button")!).onclick = loadMoreComics;

    const createImgPopup = (image: HTMLImageElement) => {
        removeAllPopups();

        const popupContainer = document.createElement("div");
        popupContainer.classList.add("popup-container");
        popupContainer.onmouseleave = () => {
            popupContainer.remove();
        };
        popupContainer.onclick = () => {
            removeAllPopups();
        };

        const clone = image.cloneNode(true) as HTMLElement;
        clone.classList.remove("normal-img");
        clone.classList.add("popup-img");

        const closeButton = document.createElement("img");
        closeButton.classList.add("close-button");
        closeButton.src = "/static/img/close.svg?v=0";

        popupContainer.appendChild(clone);
        popupContainer.appendChild(closeButton);
        image.parentNode!.appendChild(popupContainer);
    };

    // add links to comics list
    comics.concat(links.split("\n")); // first 50 comics 29.11.2020 - 17.01.21
    addLinksToComics();

    const today = dateIncreaseByDays(getToday(), 1);
    setCurrentComic(today);
    currentImg.onerror = () => {
        dateIncreaseByDays(today, -1);
        setCurrentComic(today);

        if (loaded < comicCountToLoadOnCLick) {
            loaded++;
        }
    };
}

const startButton = document.getElementById("start-button-no_3rd_party");
if (startButton !== null) {
    const contentContainer = document.getElementById(
        "comic-content-container",
    )!;
    // no_3rd_party is activated
    startButton.onclick = () => {
        startButton.remove();
        contentContainer.classList.remove("hidden");
        startLoadingComics();
    };
    contentContainer.classList.add("hidden");
} else {
    startLoadingComics();
}
// @license-end
