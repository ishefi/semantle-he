let cache = {};
let darkModeMql = window.matchMedia('(prefers-color-scheme: dark)');
let darkMode = false;

function getSolverCountStory(beforePronoun) {
    let solverCountStory = "";
    if (localStorage.getItem("solverCount"))  {
        const solversBefore = parseInt(localStorage.getItem("solverCount"));
        if (solversBefore === 0) {
            solverCountStory = `🤩 מקום ראשון! 🤩`;
            if (Math.random() >= 0.5) {
               solverCountStory += ` אף אחת לא פתרה`;
            } else {
                solverCountStory += ` אף אחד לא פתר`;
            }
        } else if (solversBefore === 1) {
            if (Math.random() >= 0.5) {
               solverCountStory = `רק אחת פתרה`;
            } else {
                solverCountStory = `רק אחד פתר`;
            }
        } else {
            solverCountStory = `רק ${solversBefore} פתרו`;
        }
        solverCountStory += ` היום את סמנטעל ${beforePronoun}!`;
    }
    return solverCountStory;
}


function solveStory(guesses, puzzleNumber) {
//    if (guess_count == 0) {
//        return `I gave up on Semantle ${puzzleNumber} without even guessing once.`;
//    }

//    if (guess_count == 1) {
//        return `I got Semantle ${puzzleNumber} on my first guess!`;
//    }

    txt = 'פתרתי את סמנטעל #' + puzzleNumber + ' ב־' + guesses.length + ' ניחושים!\n';
    txt += getSolverCountStory('לפני');
    txt += '\nhttps://semantle.ishefi.com\n';
    let shareGuesses = guesses.slice();
    shareGuesses.sort(function(a, b){return b.similarity-a.similarity});
    shareGuesses = shareGuesses.slice(0, 6);
    let greens = 0;
    let whites = 0;
    let squares = 5;
    shareGuesses.forEach(entry => {
        let {similarity, guess, guess_number, distance, egg} = entry;
        greens = Math.max(Math.floor(squares * distance / 1000), 0);
        whites = squares - greens;
        if (egg) {
            txt += '✨'.repeat(squares);
        }
        else {
            txt += '🟩'.repeat(greens) + '⬜'.repeat(whites) + ' ';
        }
        txt += ' ' + guess_number;
        if (greens != 0) {
            txt += ' (' + distance + '/1000)';
        }
        txt += '\n'
    }
    );

    return txt;
}

function share() {
    // We use the stored guesses here, because those are not updated again
    // once you win -- we don't want to include post-win guesses here.
    const text = solveStory(JSON.parse(window.localStorage.getItem("guesses")), puzzleNumber.innerText);
    const copied = ClipboardJS.copy(text);

    if (copied) {
        alert("העתקת, אפשר להדביק ברשתות החברתיות!");
    }
    else {
        alert("Failed to copy to clipboard");
    }
}

function shareBtc() {
    const BTCAddress = "bc1qe3hpdddft34lmm7g6s6u6pef6k6mz4apykrla3jewapxeup4hpwsydhgx0";
    const copied = ClipboardJS.copy(BTCAddress);
    if (copied) {
        alert("copied BTC wallet address :)");
    }
    else {
        alert("Failed to copy to clipboard");
    }
}

let Semantle = (function() {
    'use strict';

    let guessed = new Set();
    let firstGuess = true;
    let guesses = [];
    let guessCount = 1;
    let gameOver = false;
    const handleStats = false;
    const storage = window.localStorage;
    let notificationId = null;

//    TODO: use value sent from BE ?
    const day_ms = 86400000;
    const now = Date.now();
    const today = Math.floor(now / day_ms);
    const initialDay = 19044;
    const puzzleNumber = today + 1 - initialDay;
    const tomorrow = new Date();
    tomorrow.setUTCHours(24, 0, 0, 0);

    function includeHTML() {
  var z, i, elmnt, file, xhttp;
  /* Loop through a collection of all HTML elements: */
  z = document.getElementsByTagName("*");
  for (i = 0; i < z.length; i++) {
    elmnt = z[i];
    /*search for elements with a certain atrribute:*/
    file = elmnt.getAttribute("w3-include-html");
    if (file) {
      /* Make an HTTP request using the attribute value as the file name: */
      xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
          if (this.status == 200) {elmnt.innerHTML = this.responseText;}
          if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
          /* Remove the attribute, and call this function once more: */
          elmnt.removeAttribute("w3-include-html");
          includeHTML();
        }
      }
      xhttp.open("GET", file, true);
      xhttp.send();
      /* Exit the function: */
      return;
    }
  }
}

    includeHTML();

    async function getSim(word) {
        if (cache.hasOwnProperty(word)) {
            let cached = cache[word];
            cached.guess = word;
            return cached;
        }
        const url = "/api/distance" + '?word=' + word;
        const response = await fetch(url, {headers: new Headers({'X-SH-Version': "2023-09-10"})});
        try {
            if (response.status === 200) {
                return await response.json();
            }
        } catch (e) {

        }
    }

    function guessRow(similarity, oldGuess, percentile, guessNumber, guess, egg) {  // TODO: simplify method's signature
    let percentileText = "(רחוק)";
    let progress = "";
    let cls = "";
    if (egg) {
        percentileText = egg;
    }
    if (percentile > 0) {
        if (percentile == 1000) {
            percentileText = "מצאת!";
        } else {
            cls = "close";
            percentileText = `<span style="text-align:right; width:5em; display:inline-block;">${percentile}/1000</span>&nbsp;`;
            progress = ` <span class="progress-container">
<span class="progress-bar" style="width:${percentile/10}%">&nbsp;</span>
</span>`;
        }
    }
    let color;
    if (oldGuess === guess) {
        color = '#c0c';
    } else if (darkMode) {
        color = '#fafafa';
    } else {
        color = '#000';
    }
    if (similarity == null) return '';
    return `<tr><td>${guessNumber}</td>
    <td style="color:${color}" onclick="select('${oldGuess}', secretVec);">${oldGuess}</td>
    <td align="right" dir="ltr">${similarity.toFixed(2)}</td>
    <td class="${cls}">${percentileText}${progress}
</td></tr>`;

}

    function checkMedia() {
        const storagePrefersDarkColorScheme = storage.getItem("prefersDarkColorScheme");
        if (storagePrefersDarkColorScheme === 'true' || storagePrefersDarkColorScheme === 'false') {
            darkMode = storagePrefersDarkColorScheme === 'true';
        } else {
            darkMode = darkModeMql.matches;
            darkModeMql.onchange = (e) => {
                darkMode = e.matches;
                toggleDarkMode(darkMode)
                updateGuesses();
            }
        }
        toggleDarkMode(darkMode);
    }

    function saveGame(guessCount, winState) {
        // If we are in a tab still open from yesterday, we're done here.
        // Don't save anything because we may overwrite today's game!
        let savedPuzzleNumber = storage.getItem("puzzleNumber");
        if (savedPuzzleNumber != puzzleNumber) { return }

        storage.setItem("winState", winState);
        storage.setItem("guesses", JSON.stringify(guesses));
    };

    function openRules() {
        document.body.classList.add('rules-open');
        storage.setItem("readRules", true);
    }
    function openSettings() {
        document.body.classList.add('dialog-open', 'settings-open');
        $("#settings-close")[0].focus();
    }
    function openNotification() {
        document.body.classList.add("notification-open");
        storage.setItem("notification-" + notificationId, true);
    }

    function updateGuesses(newGuess) {
        let inner = `<tr>
        <th>#</th>
        <th>ניחוש</th>
        <th>קרבה</th>
        <th>מתחמם?</th></tr>`;
        /* This is dumb: first we find the most-recent word, and put
           it at the top.  Then we do the rest. */
       var i;
        for (i = 0; i < guesses.length; i++) {
            let entry = guesses[i];
            if (entry.guess == newGuess) {
                inner += guessRow(entry.similarity, entry.guess, entry.distance, entry.guess_number, newGuess, entry.egg);
                break;
            }
        }
        inner += "<tr><td colspan=4><hr></td></tr>";
        for (i = 0; i < guesses.length; i++) {
            let entry = guesses[i];
            if (entry.guess != newGuess) {
                inner += guessRow(entry.similarity, entry.guess, entry.distance, entry.guess_number, newGuess, entry.egg);
            }
        }
        $('#guesses')[0].innerHTML = inner;
        twemoji.parse($('#guesses')[0]);
    }

    function fetchGuesses() {
        let fixed = []
        let storedGuesses = JSON.parse(storage.getItem("guesses"));
        for (let entry of storedGuesses) {
          if (entry instanceof Array) {
            entry = {
                similarity: entry[0],
                guess: entry[1],
                guess_number: entry[2],
                distance: entry[3],
                egg: entry[4]
            }
          }
          fixed.push(entry);
        }
       return fixed;
    }

    function toggleDarkMode(on) {
        document.body.classList[on ? 'add' : 'remove']('dark');
        const darkModeCheckbox = $("#dark-mode")[0];
        // this runs before the DOM is ready, so we need to check
        if (darkModeCheckbox) {
            darkModeCheckbox.checked = on;
        }
    }

    function addEventListenersWhenMenuAppears() {
    const profileImage = document.getElementById("profile-image");
    const tooltipMenu = document.getElementById("tooltip-menu");
    const logoutLink = document.getElementById("logout-link");


    function toggleTooltipMenu() {
        tooltipMenu.style.display = tooltipMenu.style.display === "block" ? "none" : "block";
    }

    if (profileImage && tooltipMenu && logoutLink) {
        // Event listener for clicking the profile image
        profileImage.addEventListener("click", function (event) {
            event.stopPropagation(); // Prevent the click event from propagating to the document
            toggleTooltipMenu();
        });

        // Event listener for clicking anywhere outside the tooltip menu
        document.addEventListener("click", function (event) {
            if (event.target !== tooltipMenu && event.target !== profileImage) {
                tooltipMenu.style.display = "none";
            }
        });
        // Event listener for clicking the logout link
        logoutLink.addEventListener("click", function (event) {
          event.preventDefault(); // Prevent the link from navigating
          localStorage.clear();
          window.location.href = "/logout";
        });
    } else {
        // The "menu" element is not yet available, so set up a MutationObserver to wait for it
        const observer = new MutationObserver(function (mutationsList) {
            for (const mutation of mutationsList) {
                if (mutation.type === "childList" && mutation.addedNodes) {
                    for (const addedNode of mutation.addedNodes) {
                        if (addedNode.id === "menu") {
                            // "menu" element is now available, remove the observer and add event listeners
                            observer.disconnect();
                            addEventListenersWhenMenuAppears();
                            return;
                        }
                    }
                }
            }
        });

        // Start observing changes in the DOM
        observer.observe(document.body, { childList: true, subtree: true });
    }
}

// Call the function to add event listeners when the "menu" element appears
addEventListenersWhenMenuAppears();



    async function init() {
        let notification = document.getElementById("notification");
        let popupBlocks = ["rules"];
        if (notification) {
            notificationId = notification.dataset.notificationid;
            popupBlocks.push("notification");
        }
        if (!storage.getItem("readRules")) {
            openRules();
        } else if (notificationId) {
           let seenNotification = storage.getItem("notification-" + notificationId);
           let expiry = Date.parse(notification.dataset.notificationexpire) / day_ms;
           let expired = today > expiry;
           if (!(seenNotification || expired)) {
                openNotification();
           }
        }

        $("#rules-button")[0].addEventListener('click', openRules);
        $("#settings-button")[0].addEventListener('click', openSettings);

        popupBlocks.forEach((blockType) => {
            let blockId = "#" + blockType + "-";
            [$(blockId + "underlay"), $(blockId + "close")].forEach((el) => {
                el[0].addEventListener('click', () => {
                    document.body.classList.remove(blockType + '-open');
                });
            });
        });

        $("#rules")[0].addEventListener("click", (event) => {
            // prevents click from propagating to the underlay, which closes the rules
            event.stopPropagation();
        });


        document.querySelectorAll(".dialog-underlay, .dialog-close, #capitalized-link").forEach((el) => {
            el.addEventListener('click', () => {
                document.body.classList.remove('dialog-open', 'rules-open', 'settings-open');
            });
        });

        document.querySelectorAll(".dialog").forEach((el) => {
                el.addEventListener("click", (event) => {
                    // prevents click from propagating to the underlay, which closes the rules
                    event.stopPropagation();
                });
            });

        // accordion functionality taken from
        // https://www.w3schools.com/howto/howto_js_accordion.asp
        document.querySelectorAll(".accordion").forEach((el) => {
          el.addEventListener("click", function() {
            this.classList.toggle("active");

            const panel = this.nextElementSibling;
            if (panel.style.display === "block") {
              panel.style.display = "none";
            } else {
              panel.style.display = "block";
            }
          });
        });

        $("#dark-mode")[0].addEventListener('click', function(event) {
            storage.setItem("prefersDarkColorScheme", event.target.checked);
            darkModeMql.onchange = null;
            darkMode = event.target.checked;
            toggleDarkMode(darkMode);
            updateGuesses();
        });

        toggleDarkMode(darkMode);

        if (storage.getItem("prefersDarkColorScheme") === null) {
            $("#dark-mode")[0].checked = false;
            $("#dark-mode")[0].indeterminate = true;
        }

        let form = $('#form')[0];
        if (form === undefined) return;

        function dealWithHistory(guessHistory) {
          if (!guessHistory || guessHistory.length <= 1) {
            return;
          }
          guessed = new Set();
          guesses = []
          for (var i = 0; i < guessHistory.length - 1; i++) {
            let guess = guessHistory[i];
            guessed.add(guess.guess);
            guesses.push(guess);
          }
          guessCount = guessed.size + 1;
        }

        function dealWithGuess(entry) {
            let {similarity, guess, distance, egg} = entry;
            if ((!guessed.has(guess)) && (similarity != null)) {
                guessed.add(guess);
                if (!entry.guess_number) {
                  entry.guess_number = guessCount
                }
                guesses.push(entry);
                guessCount += 1;
                if (distance == 1000){
                    endGame(true, true);
                }
            }
            guesses.sort(function(a, b){return b.similarity-a.similarity});
            if (!gameOver){
                saveGame(-1, -1);
            }
            updateGuesses(guess);
            firstGuess = false;
        }

        $('#form')[0].addEventListener('submit', async function(event) {
            event.preventDefault();
            $('#guess').focus();
            $('#error')[0].textContent = "";
            let guess = $('#guess')[0].value.trim().replace("!", "").replace("*", "");
            if (!guess) {
                return false;
            }

            const allGuessData = await getSim(guess);
            let guessData = null;
            if (allGuessData) {
              guessData = allGuessData[allGuessData.length - 1];
            }
            if (guessData == null || guessData.similarity === null) {
                $('#error')[0].textContent = `אני לא מכיר את המילה ${guess}.`;
                $('#guess')[0].select();
                return false;
            }

            $('#guess')[0].value = "";

            let score = guessData.similarity;
            const distance = guessData.distance;
            let egg = guessData.egg;
            let toCache = Object.assign({}, guessData);
            toCache.guess_number = 0;
            cache[guess] = toCache; // TODO: deal with history as well
            storage.setItem("cache", JSON.stringify(cache));
            if (guessData.solver_count != null) {
                storage.setItem("solverCount", JSON.stringify(guessData.solver_count));
            }
            dealWithHistory(allGuessData);
            dealWithGuess(guessData);
            return false;
        });

//        let puzzleNumber = $("#puzzleNumber")[0].innerText;
        let storagePuzzleNumber = storage.getItem("puzzleNumber");
        if (storagePuzzleNumber != puzzleNumber) {
            storage.removeItem("guesses");
            storage.removeItem("cache");
            storage.removeItem("winState");
            storage.setItem("puzzleNumber", puzzleNumber);
        }

        const winState = storage.getItem("winState");
        if (winState != null) {
            guesses = fetchGuesses();
            cache = JSON.parse(storage.getItem("cache")) || {};
            guesses.sort(function(a, b){return b.similarity-a.similarity});
            for (let guess of guesses) {
                guessed.add(guess.guess);
            }
            guessCount = guesses.length + 1;
            updateGuesses("");
            if (winState != -1) {
                endGame(winState);
            }
        }

        let oldGuessesStr = $("#old_guesses")[0].innerText;
        if (oldGuessesStr && oldGuessesStr.length > 1) {
             let oldGuesses = JSON.parse(oldGuessesStr);
             oldGuesses.forEach(guess => {
                dealWithGuess(guess);
             });
         }

            var x = setInterval(function() {
                // Find the distance between now and the count down date
                var distance = tomorrow.getTime() - Date.now();
                if (distance < 0 && (!document.hidden)) {
                    window.location.replace(location.protocol + '//' + location.host + location.pathname);
                    return;
                }

                // Time calculations for days, hours, minutes and seconds
                var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);

                // Output the result in an element with id="demo"
                document.getElementById("timer").innerHTML = "הסמנטעל הבא בעוד " +
                hours + ":" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');

                // If the count down is over, write some text
            }, 1000);
            if (window.location.host === 'semantle-he.herokuapp.com') {
              window.location.replace("https://semantle.ishefi.com?guesses=" + JSON.stringify(guesses));
            }
            twemoji.parse(document.body);
        } // end init

        function endGame(won, countStats) {
        let stats;
        if (handleStats) {
            stats = getStats();
            if (countStats) {
                const onStreak = (stats['lastEnd'] == puzzleNumber - 1);

                stats['lastEnd'] = puzzleNumber;
                if (won) {
                    if (onStreak) {
                        stats['winStreak'] += 1;
                    } else {
                    stats['winStreak'] = 1;
                    }
                    stats['wins'] += 1;
                } else {
                    stats['winStreak'] = 0;
                    stats['giveups'] += 1;
                }
                storage.setItem("stats", JSON.stringify(stats));
            }
        }

        gameOver = true;
        document.getElementById("timer").hidden = false;
        let response;

        const solverCountStory = getSolverCountStory("לפניך");

        if (won) {
            response = `<p><b>
            ניצחת!
            מצאת את הפתרון תוך ${guesses.length} ניחושים!
             ${solverCountStory}
            אפשר להמשיך לנסות להכניס מילים ולראות את הקרבה שלהן,
            וגם <a href="javascript:share();">לשתף</a>
            ולחזור לשחק מחר.
            </b>
            <br>
            </p>
            <p align="left">
             ואם ממש בא לך,
             <br/>
             <a href="https://ko-fi.com/ishefi" target="_blank" style="text-decoration: none;">אפשר גם לקנות לי ☕</a>,
             <br/>
             לשחק ב<a href="https://degle.ishefi.com" target="_blank" style="text-decoration: none;">דעגעל🚩</a>
             <br/>
             או ב־<a href="https://mimamu.ishefi.com" target="_blank" style="text-decoration: none;">MiMaMu</a>
             <br/>
             או לעקוב אחרי <a href="https://sufganiyot.ishefi.com" target="_blank" style="text-decoration: none;">כמה סופגניות אכלתי </a>
             <br/>
             עד הסמנטעל הבא
             </p>`
        } else {
        // right now we do not allow giving up
            response = `<p><b>You gave up!  The secret word is: ${secret}</b>.  Feel free to keep entering words if you are curious about the similarity to other words.  You can see the nearest words <a href="nearby_1k/${secretBase64}">here</a>.</p>`;
        }

        if (handleStats) {
            const totalGames = stats['wins'] + stats['giveups'] + stats['abandons'];
            response += `<br/>
Stats (since we started recording, on day 23): <br/>
<table>
<tr><th>First game:</th><td>${stats['firstPlay']}</td></tr>
<tr><th>Total days played:</th><td>${totalGames}</td></tr>
<tr><th>Wins:</th><td>${stats['wins']}</td></tr>
<tr><th>Win streak:</th><td>${stats['winStreak']}</td></tr>
<tr><th>Give-ups:</th><td>${stats['giveups']}</td></tr>
<tr><th>Did not finish</th><td>${stats['abandons']}</td></tr>
<tr><th>Total guesses across all games:</th><td>${stats['totalGuesses']}</td></tr>
</table>
`;
        }
        $('#response')[0].innerHTML = response;
        twemoji.parse($('#response')[0]);
        if (endGame) {
            saveGame(guesses.length, won ? 1 : 0);
        }
    }

        return {
        init: init,
        checkMedia: checkMedia,
    };
})();

// do this when the file loads instead of waiting for DOM to be ready to avoid
// a flash of unstyled content
Semantle.checkMedia();

const observer = new MutationObserver((mutations, obs) => {
  let includees = document.querySelectorAll('[w3-include-html]');
  if (includees.length == 0) {
    Semantle.init();
    obs.disconnect();
    return;
  }
});

observer.observe(document, {
  childList: true,
  subtree: true
});
