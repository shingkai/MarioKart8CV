let raceTracker;
let controls;
let ws;
let currentRaceId = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:3000');

    ws.onopen = () => {
        console.log('Connected to server');
        reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'raceUpdate':
                    currentRaceId = data.raceId;
                    const formattedPositions = data.positions.map(p => ({
                        id: p.player_id,
                        position: p.position
                    }));
                    raceTracker.updatePositions(formattedPositions);
                    break;

                case 'error':
                    console.error('Server error:', data.message);
                    break;
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    };

    ws.onclose = () => {
        console.log('Disconnected from server');
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            setTimeout(() => {
                reconnectAttempts++;
                console.log(`Reconnecting... Attempt ${reconnectAttempts}`);
                connectWebSocket();
            }, RECONNECT_DELAY);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

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

function startRace() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWebSocket();
    }
}

function stopRace() {
    if (ws) {
        ws.close();
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
        () => {}, // Scenario handling removed
        () => {}  // Speed control removed as we're using real-time updates
    );
});