let raceTracker;
let controls;
let raceInterval;
let currentSpeed = 1000; // Default speed

function shufflePositions(scenario) {
    const newPositions = [...raceTracker.positions];

    switch (scenario) {
        case 'blueShell':
            if (Math.random() < 0.3) {
                const leader = newPositions.shift();
                newPositions.push(leader);
            }
            break;

        case 'catchup':
            if (Math.random() < 0.4) {
                const idx = Math.floor(Math.random() * 3) + 4;
                if (idx < newPositions.length) {
                    const racer = newPositions[idx];
                    newPositions.splice(idx, 1);
                    newPositions.splice(Math.max(0, idx - 2), 0, racer);
                }
            }
            break;

        case 'breakaway':
            if (Math.random() < 0.3) {
                const topThree = newPositions.slice(0, 3);
                const rest = newPositions.slice(3);
                topThree.sort(() => Math.random() - 0.5);
                return [...topThree, ...rest];
            }
            break;

        default:
            if (Math.random() < 0.5) {
                const idx1 = Math.floor(Math.random() * newPositions.length);
                const idx2 = Math.floor(Math.random() * newPositions.length);
                if (Math.abs(idx1 - idx2) === 1) {
                    [newPositions[idx1], newPositions[idx2]] =
                    [newPositions[idx2], newPositions[idx1]];
                }
            }
    }

    return newPositions;
}

function startRace() {
    stopRace(); // Clear any existing interval
    raceInterval = setInterval(() => {
        const newPositions = shufflePositions(controls.currentScenario);
        raceTracker.updatePositions(newPositions);
    }, currentSpeed);
}

function stopRace() {
    if (raceInterval) {
        clearInterval(raceInterval);
    }
}

function updateSpeed(newSpeed) {
    currentSpeed = newSpeed;
    if (controls.isRacing) {
        startRace(); // Restart the interval with new speed
    }
}

document.addEventListener('DOMContentLoaded', () => {
    raceTracker = new RaceTracker('race-tracker', {
        width: 128,
        height: 400,
        margin: { top: 20, right: 20, bottom: 20, left: 20 },
        circleRadius: 24,
        circleSpacing: 56
    });

    controls = new RaceControls(
        'controls',
        startRace,
        stopRace,
        (scenario) => controls.currentScenario = scenario,
        updateSpeed // Add speed change handler
    );
});