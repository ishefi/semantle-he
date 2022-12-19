const cache = {};
let darkModeMql = window.matchMedia('(prefers-color-scheme: dark)');
let darkMode = false;

function solveStory(guesses, puzzleNumber) {
//    if (guess_count == 0) {
//        return `I gave up on Semantle ${puzzleNumber} without even guessing once.`;
//    }

//    if (guess_count == 1) {
//        return `I got Semantle ${puzzleNumber} on my first guess!`;
//    }

    txt = 'פתרתי את סמנטעל #' + puzzleNumber + ' ב־' + guesses.length + ' ניחושים!';
    txt += '\nhttps://semantle.ishefi.com\n';
    let shareGuesses = guesses.slice();
    shareGuesses.sort(function(a, b){return b[0]-a[0]});
    shareGuesses = shareGuesses.slice(0, 6);
    let greens = 0;
    let whites = 0;
    let squares = 5;
    shareGuesses.forEach(guess => {
        [similarity, old_guess, guess_number, percentile, egg] = guess;
        greens = Math.max(Math.floor(squares * percentile / 1000), 0);
        whites = squares - greens;
        if (egg) {
            txt += '✨'.repeat(squares);
        }
        else {
            txt += '🟩'.repeat(greens) + '⬜'.repeat(whites) + ' ';
        }
        txt += ' ' + guess_number;
        if (greens != 0) {
            txt += ' (' + percentile + '/1000)';
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

let Semantle = (function() {
    'use strict';

    let guessed = new Set();
    let firstGuess = true;
    let guesses = [];
    let guessCount = 1;
    let gameOver = false;
    const handleStats = false;
    const storage = window.localStorage;

//    TODO: use value sent from BE ?
    const now = Date.now();
    const today = Math.floor(now / 86400000);
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
            return cache[word];
        }
        const url = "/api/distance" + '?word=' + word;
        const response = await fetch(url);
        try {
            return await response.json();
        } catch (e) {
            return null;
        }
    }

    function guessRow(similarity, oldGuess, percentile, guessNumber, guess, egg) {
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
    if (similarity === null) return '';
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

    function updateGuesses(guess) {
        let inner = `<tr>
        <th>#</th>
        <th>ניחוש</th>
        <th>קרבה</th>
        <th>מתחמם?</th></tr>`;
        /* This is dumb: first we find the most-recent word, and put
           it at the top.  Then we do the rest. */
        for (let entry of guesses) {
            let [similarity, oldGuess, guessNumber, percentile, egg] = entry;
            if (oldGuess == guess) {
                inner += guessRow(similarity, oldGuess, percentile, guessNumber, guess, egg);
            }
        }
        inner += "<tr><td colspan=4><hr></td></tr>";
        for (let entry of guesses) {
            let [similarity, oldGuess, guessNumber, percentile, egg] = entry;
            if (oldGuess != guess) {
                inner += guessRow(similarity, oldGuess, percentile, guessNumber, guess, egg);
            }
        }
        $('#guesses')[0].innerHTML = inner;
    }

    function toggleDarkMode(on) {
        document.body.classList[on ? 'add' : 'remove']('dark');
        const darkModeCheckbox = $("#dark-mode")[0];
        // this runs before the DOM is ready, so we need to check
        if (darkModeCheckbox) {
            darkModeCheckbox.checked = on;
        }
    }

    async function init() {
        if (!storage.getItem("readRules")) {
            openRules();
        }

        $("#rules-button")[0].addEventListener('click', openRules);
        $("#settings-button")[0].addEventListener('click', openSettings);

        [$("#rules-underlay"), $("#rules-close")].forEach((el) => {
            el[0].addEventListener('click', () => {
                document.body.classList.remove('rules-open');
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

        function dealWithGuess(entry) {
            let [similarity, guess, _, distance, egg] = entry;
            if (!guessed.has(guess)) {
                guessCount += 1;
                guessed.add(guess);

                guesses.push(entry);
                if (distance == 1000){
                    endGame(true, true);
                }
            }
            guesses.sort(function(a, b){return b[0]-a[0]});
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

            const guessData = await getSim(guess);
            if (guessData.similarity === null) {
                $('#error')[0].textContent = `אני לא מכיר את המילה ${guess}.`;
                $('#guess')[0].select();
                return false;
            }

            $('#guess')[0].value = "";

            let score = guessData.similarity;
            const distance = guessData.distance;
            let egg = guessData.egg;
            cache[guess] = guessData;

            const newEntry = [score, guess, guessCount, distance, egg];
            dealWithGuess(newEntry);
//            if (guess.toLowerCase() === secret && !gameOver) {
//                endGame(guesses.length);
//            }
            return false;
        });

//        let puzzleNumber = $("#puzzleNumber")[0].innerText;
        let storagePuzzleNumber = storage.getItem("puzzleNumber");
        if (storagePuzzleNumber != puzzleNumber) {
            storage.removeItem("guesses");
            storage.removeItem("winState");
            storage.setItem("puzzleNumber", puzzleNumber);
        }

        const winState = storage.getItem("winState");
        if (winState != null) {
            guesses = JSON.parse(storage.getItem("guesses"));
            guesses.sort(function(a, b){return b[0]-a[0]});
            for (let guess of guesses) {
                guessed.add(guess[1]);
            }
            guessCount = guessed.size;
            updateGuesses("");
            if (winState != -1) {
                endGame(winState);
            }
        }

        // let oldGuessesStr = $("#old_guesses")[0].innerText;
        // if (oldGuessesStr && oldGuessesStr.length > 1) {
        //     let oldGuesses = JSON.parse(oldGuessesStr);
        //     oldGuesses.forEach(guess => {dealWithGuess(guess)});
        // }

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
        if (won) {
            response = `<p><b>
            ניצחת!
            מצאת את הפתרון תוך ${guesses.length} ניחושים!
            אפשר להמשיך לנסות להכניס מילים ולראות את הקרבה שלהן,
            וגם <a href="javascript:share();">לשתף</a>
            ולחזור לשחק מחר.
            </b>
            <br>
            </p>
            <p align="left">
             (ואם ממש בא לך, <a href="https://ko-fi.com/ishefi" target="_blank" style="text-decoration: none;">אפשר גם לקנות לי ☕</a>, 
             לשחק ב<a href="https://degle.ishefi.com" target="_blank" style="text-decoration: none;">דעגעל🚩</a>
             או לעקוב אחרי <a href="https://sufganiyot.ishefi.com" target="_blank" style="text-decoration: none;">כמה סופגניות אכלתי </a>
             עד הסמנטעל הבא)
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
