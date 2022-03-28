// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0
function removeAllPopups() {
    for (let node of d.getElementsByClassName("popup-container")) {
        node.remove();
    }
}

function startLoadingComics() {
    // date with special link format:
    const wrongLinks = [
        [
            getDateBy(2021, 5, 25),
            "administratives/kaenguru-comics/25/original/"
        ],
        [
            getDateBy(2021, 9, 6),
            "administratives/kaenguru-comics/2021-09/6/original/"
        ],
        [
            getDateBy(2021, 10, 4),
            "administratives/kaenguru-comics/2021-10/4/original"
        ],
        [
            getDateBy(2021, 10, 29),
            "administratives/kaenguru-comics/29/original"
        ],
        [
            getDateBy(2021, 11, 3),
            "administratives/kaenguru-comics/2021-11/03-11-21/original"
        ],
        [
            getDateBy(2021, 12, 6),
            "administratives/kaenguru-comics/2021-12/6/original"
        ],
        [
            getDateBy(2022, 1, 29),
            "administratives/kaenguru-comics/2022-01/29-3/original"
        ],
        [
            getDateBy(2022, 2, 7),
            "administratives/kaenguru-comics/08-02-22/original"
        ],
        [
            getDateBy(2022, 2, 12),
            "administratives/kaenguru-comics/12/original"
        ],
        [
            getDateBy(2022, 2, 14),
            "administratives/kaenguru-comics/14/original"
        ],
        [
            getDateBy(2022, 3, 28),
            "administratives/kaenguru-comics/2022-03/kaenguru-2022-03-28/original"
        ]
    ];

    const comics = [];

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
    function addLinksToComics() {
        const today = getToday();
        const date = copyDate(firstDateWithNewLink);
        while (date.getTime() <= today.getTime()) {
            comics.push(generateComicLink(date));
            dateIncreaseByDays(date, 1);
        }
    }

    const currentImgHeader = elById("current-comic-header");
    const currentImg = elById("current-img");

    //const currentImgContainer = elById("current-img-container");
    function setCurrentComic(date) {
        let link = generateComicLink(date);
        link = link.startsWith("/") ? link : "https://img.zeit.de/" + link
        currentImg.src = link;
        currentImgHeader.innerText = "Neuster " + getDateString(date) + ":";
        currentImgHeader.href = link;
    }

    function getDateString(date) {
        return "Comic von "
            + getDayName(date) + ", dem "
            + date.getDate() + ". "
            + getMonthName(date) + " "
            + date.getFullYear();
    }

    const days = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];

    function getDayName(date) {
        return days[date.getDay()];
    }

    const months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];

    function getMonthName(date) {
        return months[date.getMonth()];
    }

    const firstDateWithOldLink = getDateBy(2020, 12, 3);
    const oldLinkRegex = /administratives\/kaenguru-comics\/kaenguru-(\d{2,3})(?:-2)?\/original\/?/;

    const firstDateWithNewLink = getDateBy(2021, 1, 19);
    const newLinkRegex = /administratives\/kaenguru-comics\/(\d{4})-(\d{2})\/(\d{2})\/original\/?/;

    const relativeLinkRegex = /\/static\/img\/(\d{4})-(\d{1,2})-(\d{1,2})\.jpg/;

    function getDateFromLink(link) {
        for (const reg of [newLinkRegex, relativeLinkRegex]) {
            // urls with year, month, day in them as three groups
            const match = link.toLowerCase().match(reg);
            if (match && match.length > 3) {
                return getDateBy(match[1], match[2], match[3]);
            }
        }
        // urls with incrementing number in them
        let arr = link.toLowerCase().match(oldLinkRegex);
        if (arr && arr.length > 1) {
            const num = arr[1] - 5;
            let date = new Date(firstDateWithOldLink.getTime());
            for (let i = 0; i < num; i++) {
                date.setTime(dateIncreaseByDays(date, isSunday(date) ? 2 : 1));
            }
            return isSunday(date) ? dateIncreaseByDays(date, 1) : date;
        }
        link = link.toLowerCase().trim()
        switch (link) {  // first urls with special format
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
            if (link === arr[1]) return arr[0];
        }
    }

    const linkFormat = "administratives/kaenguru-comics/%y-%m/%d/original"

    function generateComicLink(date) {
        for (const arr of wrongLinks) {
            if (datesEqual(date, arr[0])) return arr[1];
        }
        let month = (date.getMonth() + 1).toString();
        let day = date.getDate().toString();
        return linkFormat.replace("%y", date.getFullYear().toString())
            .replace("%m", month.length === 2 ? month : "0" + month)
            .replace("%d", day.length === 2 ? day : "0" + day);
    }

    function isSunday(date) {
        return date
            && date.getDay() === 0
            // exception for 2020-12-20 (sunday) because there was a comic
            && !dateEquals(date, 2020, 12, 20);
    }

    function datesEqual(date1, date2) {
        return dateEquals(date1, date2.getFullYear(), date2.getMonth() + 1, date2.getDate());
    }

    function dateEquals(date, year, month, dayOfMonth) {
        return date.getFullYear() === year
            && date.getMonth() === month - 1
            && date.getDate() === dayOfMonth;
    }

    const millisOfOneDay = 1000 * 60 * 60 * 24;

    function dateIncreaseByDays(date, days) {
        date.setTime(date.getTime() + (days * millisOfOneDay));
        date.setHours(6); // to compensate errors through daylight savings time
        return date;
    }

    function copyDate(date) {
        return getDateBy(date.getFullYear(), date.getMonth() + 1, date.getDate());
    }

    function getDateBy(year, month, dayOfMonth) {
        return new Date(year, month - 1, dayOfMonth, 6, 0, 0, 0);
    }

    function getToday() {
        return copyDate(new Date());
    }

    const comicCountToLoadOnCLick = 7;
    const loadButton = elById("load-button");
    const list = elById("old-comics-list");
    let loaded = 0;

    function loadMoreComics() {
        for (let i = 0; i < comicCountToLoadOnCLick; i++) {
            loaded++;
            const c = comics.length - loaded;
            if (c < 0) break;

            let link = comics[c];
            const date = getDateFromLink(link);
            link = link.startsWith("/") ? link : "https://img.zeit.de/" + link;

            const listItem = d.createElement("li");
            const header = d.createElement("a");
            header.rel = "noreferrer";
            header.classList.add("comic-header");
            header.innerText = getDateString(date) + ":";
            header.href = link;
            header.style.fontSize = "25px";
            listItem.appendChild(header);
            listItem.appendChild(d.createElement("br"));
            const image = d.createElement("img");
            image.classList.add("normal-img")
            image.src = link;
            image.alt = getDateString(date);
            image.onclick = () => createImgPopup(image);
            image.onerror = () => {
                if (isSunday(date)) {
                    // normally the image is not available on sundays
                    // so we can remove the image if it is not available
                    list.removeChild(listItem);
                } else {
                    // if the image is not available, display an error message
                    listItem.append(" konnte nicht geladen werden.");
                }
            }
            listItem.appendChild(image);
            list.appendChild(listItem);
        }

        if (loaded >= comics.length) {
            loadButton.style.opacity = "0";
            loadButton.style.visibility = "invisible";
        }
    }
    elById("load-button").onclick = loadMoreComics;
    log(elById("load-button").onclick)

    function createImgPopup(image) {
        removeAllPopups();

        const popupContainer = d.createElement("div");
        popupContainer.classList.add("popup-container");
        popupContainer.onmouseleave = () => {
            popupContainer.remove();
        }
        popupContainer.onclick = () => {
            removeAllPopups();
        }

        const clone = image.cloneNode(true);
        clone.classList.remove("normal-img");
        clone.classList.add("popup-img");


        const closeButton = d.createElement("img");
        closeButton.classList.add("close-button");
        closeButton.src = "/static/img/close.svg?v=0";

        popupContainer.appendChild(clone);
        popupContainer.appendChild(closeButton);
        image.parentNode.appendChild(popupContainer);
    }

    // add links to comics list
    comics.push.apply(comics, links.split("\n")); //first 50 comics 29.11.2020 - 17.01.21
    addLinksToComics();

    const today = dateIncreaseByDays(getToday(), 1);
    setCurrentComic(today)
    currentImg.onerror = (event) => {
        dateIncreaseByDays(today, -1);
        setCurrentComic(today);
        if (loaded < comicCountToLoadOnCLick) loaded++;
    };
}

// @license-end
