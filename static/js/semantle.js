const cache = {};



let Semantle = (function() {
    'use strict';

    let guessed = new Set();
    let firstGuess = true;
    let guesses = [];
    let guessCount = 0;
    let gameOver = false;
    const storage = window.localStorage;

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

    function guessRow(similarity, oldGuess, percentile, guessNumber, guess) {
    let percentileText = "(רחוק)";
    let progress = "";
    let cls = "";
    if (percentile > 0) {
        if (percentile == 1000) {
            percentileText = "FOUND!";
        } else {
            cls = "close";
            percentileText = `<span style="text-align:right; width:5em; display:inline-block;">${percentile}/1000</span>&nbsp;`;
            progress = ` <span style="display:inline-block;width:10em;height:1ex; padding-bottom:1ex; background-color:#eeeeee;">
<span style="background-color:#008000; width:${percentile/10}%; display:inline-block">&nbsp;</span>
</span>`;
        }
    }
    let color;
    if (oldGuess === guess) {
        color = '#cc00cc';
    } else {
        color = '#000000';
    }
    return `<tr><td>${guessNumber}</td><td style="color:${color}" onclick="select('${oldGuess}', secretVec);">${oldGuess}</td><td>${similarity.toFixed(2)}</td><td class="${cls}">${percentileText}${progress}
</td></tr>`;

}

    function saveGame(winState) {
        let oldState = storage.getItem("winState");
        if (oldState == -1 || oldState == null) {
            storage.setItem("winState", winState);
            storage.setItem("guesses", JSON.stringify(guesses));
        }
    }

    function updateGuesses(guess) {
        let inner = `<tr><th>#</th><th>ניחוש</th><th>דמיון</th><th>מתחמם?</th></tr>`;
        /* This is dumb: first we find the most-recent word, and put
           it at the top.  Then we do the rest. */
        for (let entry of guesses) {
            let [similarity, oldGuess, guessNumber, percentile] = entry;
            if (oldGuess == guess) {
                inner += guessRow(similarity, oldGuess, percentile, guessNumber, guess);
            }
        }
        inner += "<tr><td colspan=4><hr></td></tr>";
        for (let entry of guesses) {
            let [similarity, oldGuess, guessNumber, percentile] = entry;
            if (oldGuess != guess) {
                inner += guessRow(similarity, oldGuess, percentile, guessNumber);
            }
        }
        $('#guesses')[0].innerHTML = inner;
    }

    async function init() {
    $('#form')[0].addEventListener('submit', async function(event) {
            event.preventDefault();
            $('#guess').focus();
            $('#error').textContent = "";
            let guess = $('#guess')[0].value.trim().replace("!", "").replace("*", "");
            if (!guess) {
                return false;
            }

            $('#guess').value = "";

            const guessData = await getSim(guess);
            if (guessData.similarity < 0) {
                $('#error')[0].textContent = `אני לא מכיר את המילה ${guess}.`;
                return false;
            }

            let score = guessData.similarity;

            const distance = guessData.distance;

            cache[guess] = guessData;

            let similarity = guessData.similarity;
            if (!guessed.has(guess)) {
                guessCount += 1;
                guessed.add(guess);

                const newEntry = [similarity, guess, guessCount, distance];
                guesses.push(newEntry);
            }
            guesses.sort(function(a, b){return b[0]-a[0]});
            saveGame(-1);

            updateGuesses(guess);

            firstGuess = false;
//            if (guess.toLowerCase() === secret && !gameOver) {
//                endGame(guesses.length);
//            }
            return false;
        });
        }
        return {
        init: init
    };
})();

window.addEventListener('load', async () => { Semantle.init() });