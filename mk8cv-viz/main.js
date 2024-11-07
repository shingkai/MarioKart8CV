let raceTracker;
let controls;
let raceInterval;
let currentSpeed = 1000;
let currentRaceId = null;

async function fetchActiveRace() {
    try {
        const response = await fetch('http://localhost:3000/api/active-race');
        const data = await response.json();
        return data.raceId;
    } catch (error) {
        console.error('Error fetching active race:', error);
        return null;
    }
}

async function fetchPositions() {
    if (!currentRaceId) return;

    try {
        const response = await fetch(`http://localhost:3000/api/positions/${currentRaceId}`);
        const positions = await response.json();

        // Transform data to match our expected format
        const formattedPositions = positions.map(p => ({
            id: p.player_id,
            position: p.position
        }));

        // Update the visualization
        raceTracker.updatePositions(formattedPositions);
    } catch (error) {
        console.error('Error fetching positions:', error);
    }
}

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

async function startRace() {
    // First get the active race ID
    currentRaceId = await fetchActiveRace();
    if (!currentRaceId) {
        console.log('No active race found');
        return;
    }

    // Start polling for position updates
    raceInterval = setInterval(fetchPositions, currentSpeed);
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
        height: 700,
        margin: { top: 20, right: 20, bottom: 20, left: 20 },
        circleRadius: 24,
        circleSpacing: 56
    });

    controls = new RaceControls(
        'controls',
        startRace,
        stopRace,
        (scenario) => {}, // Scenario handling removed as we're using real data
        updateSpeed
    );
});