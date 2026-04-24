let clicks = 0;
let actualClicks = 0;
let startTime;
let isPlaying = false;
let intervalId;
let timeSelect;

document.addEventListener("DOMContentLoaded", () => {
    // Time button listeners
    document.querySelectorAll(".time-button").forEach(button => {
        button.addEventListener("click", function() {
            if (isPlaying) {
                showPopup("Error: You cannot change the time during an active game.", "error-popup");
                return;
            }
            const time = button.getAttribute("data-time");
            if (time) {
                setTime(parseFloat(time));
            } else if (button.hasAttribute("custom-time")) {
                setCustomTime();
            }
        });
    });

    // The main click object (e.g., an image)
    const clarg = document.getElementById("clarg");
    if (clarg) {
        clarg.addEventListener("click", clickHandler);
    }
    // Other initialization code can go here if needed
});

// Sets the selected game duration
function setTime(seconds) {
    timeSelect = seconds;
}

// Custom time prompt logic
function setCustomTime() {
    const customTime = prompt("Enter custom time in seconds:");
    // Handle the case where the user clicks "Cancel" or inputs nothing
    if (customTime === null || customTime.trim() === "") {
        return;
    }

    const parsedTime = parseFloat(customTime);

    // Validate the parsed time
    if (!Number.isNaN(parsedTime) && parsedTime > 1 && parsedTime <= 120) {
        timeSelect = parsedTime;
        showPopup(`Custom time set to ${parsedTime} seconds`, "game-popup");
    } else {
        showPopup("Please input a valid number between 1 and 120", "error-popup");
    }
}

// Resets the game state
function resetGame() {
    clicks = 0;
    actualClicks = 0;
    clearInterval(intervalId);
    isPlaying = false;
    document.getElementById("clicks").innerHTML = clicks;
    document.getElementById("elapsed-time").innerHTML = "0";
    document.getElementById("cps").innerHTML = "0";
}

// Starts the game timer and tracks clicks
function startGame() {
    if (timeSelect === undefined) {
        showPopup("Please select a time duration first.", "error-popup");
        return;
    }
    clicks = 0;
    actualClicks = 0;
    let cps = 0;
    startTime = Date.now();
    isPlaying = true;
    document.getElementById("clicks").innerHTML = clicks;

    intervalId = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        document.getElementById("elapsed-time").innerHTML = elapsed.toFixed(1);

        CPS(); // Calculate CPS

        // Check if game is over
        if (elapsed >= timeSelect - 0.05) {
            clearInterval(intervalId);
            isPlaying = false;
            cps = document.getElementById("cps").innerHTML;
            gameOver(cps, timeSelect); // Automatically submit the score
        }
    }, 100); // Update every 100 milliseconds
}

// Handles click events on the "Clarg" object
// Handles click events on the "Clarg" object
function clickHandler() {
    if (!isPlaying) {
        startGame();
    }

    if (isPlaying) {
        actualClicks++;
        clicks++; // Add the base click first (Total is now +1)

        const clarg = document.getElementById("clarg");
        const clargSrc = clarg.src;

        // Apply boosts directly to the global 'clicks' variable
        if (clargSrc.includes("dr_clarg")) {
            clicks = applyDrClargBoost(clicks);
        } else if (clargSrc.includes("business_clarg")) {
            clicks = applyBusinessClargBoost(clicks);
        } else if (clargSrc.includes("vacation_clarg")) {
            clicks = applyVacationClargBoost(clicks);
        } else if (clargSrc.includes("secret_clarg")) {
            clicks = applySecretClargBoost(clicks);
        } else if (clargSrc.includes("jamaican_clarg")) {
            clicks = applyJamaicanClargBoost(clicks);
        } else if (clargSrc.includes("ben_clarg")) {
            clicks = applyBenClargBoost(clicks);
        }

        // Ensure clicks is an integer (prevents floating point errors)
        clicks = Math.floor(clicks);

        document.getElementById("clicks").innerHTML = clicks;
    }
}

// Calculates Clicks Per Second
function CPS() {
    const elapsed = (Date.now() - startTime) / 1000;
    let cps;
    if (elapsed > 0) {
        cps = clicks / elapsed;
        document.getElementById("cps").innerHTML = cps.toFixed(2);
    } else {
        document.getElementById("cps").innerHTML = "0";
    }
}

// Shows the specified popup with a message
function showPopup(message, popupId) {
    const clarg = document.getElementById('clarg');
    if (clarg) clarg.removeEventListener('click', clickHandler);

    const popup = document.getElementById(popupId);
    if (popup) {
        const messageEl = popup.querySelector(".popup-message");
        if (messageEl) messageEl.innerHTML = message;
        popup.style.display = "flex";
    }
}

// Closes the specified popup
function closePopup(popupId) {
    const popup = document.getElementById(popupId);
    if (popup) {
        popup.style.display = "none";
        // If closing the game over popup, reset the game
        if (popupId === "game-popup") {
            resetGame();
            location.reload();
        }
    }
    // Re-attach listener if needed, though usually reload handles state
    const clarg = document.getElementById('clarg');
    if (clarg) clarg.addEventListener('click', clickHandler);
}

// --- Boost Functions ---

function applyDrClargBoost(currentScore) {
    // 2% chance to multiply TOTAL score by 2
    if (Math.random() < 0.02) {
        // Example: If score is 100, return 200
        return currentScore * 2;
    }
    // Otherwise, keep the score the same
    return currentScore;
}

function applyBusinessClargBoost(currentScore) {
    // 5% chance to multiply TOTAL score by 3
    if (Math.random() < 0.05) {
        return currentScore * 3;
    }
    return currentScore;
}

function applyVacationClargBoost(currentScore) {
    // 1% chance to multiply TOTAL score by 8
    if (Math.random() < 0.03) {
        return currentScore * 8;
    }
    return currentScore;
}

function applySecretClargBoost(currentScore) {
    // 1% chance to multiply TOTAL score by 1000
    if (Math.random() < 0.01) {
        return currentScore * 1000;
    }
    return currentScore;
}

function applyJamaicanClargBoost(currentScore) {
    // 1% chance to multiply TOTAL score by 1000
    if (Math.random() < 0.05) {
        return currentScore * 9;
    }
    return currentScore;
}

function applyBenClargBoost(currentScore) {
    // 10% chance to multiply TOTAL score by 0 LOL
    if (Math.random() < 0.10) {
        return currentScore * 0;
    }
    return currentScore;
}

// --- Game Over / Score Submission ---

function gameOver(cps, elapsedTime) {
    isPlaying = false;

    // Submit the score to the server
    fetch("/clargclick", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            cps: cps,
            clicks: actualClicks, // Sending actual physical clicks, not boosted
            elapsed_time: elapsedTime
        })
    })
    .then(response => response.json())
    .then(data => {
        let msg = `Time's up! You clicked ${clicks} times in ${elapsedTime} seconds with a CPS of ${cps}. `;

        if (data.message === "Score submitted successfully!") {
            msg += "Score submitted successfully!";
        } else if (data.message === "Score updated successfully!") {
            msg += "Score updated successfully!";
        } else if (data.message === "Score not higher than existing score.") {
            msg += "Score was not higher than existing score.";
        } else if (data.message === "Guest scores are not recorded.") {
            msg += "Guest scores are not recorded.";
        } else {
             msg += "Error submitting score.";
        }

        showPopup(msg, "game-popup");
    })
    .catch(error => {
        console.error("Error:", error);
        const msg = `Time's up! You clicked ${clicks} times in ${elapsedTime} seconds with a CPS of ${cps}. Error submitting score.`;
        showPopup(msg, "game-popup");
    });
}