import { SERVER_CONFIG } from './config.js';
import { RaceTracker } from './raceTracker.js';
import { RaceControls } from './controls.js';

// Export these for use in the React component
export let raceTracker;
export let controls;
export let currentRaceId;
export let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

export function connectWebSocket(raceId) {
    ws = new WebSocket(SERVER_CONFIG.WS_URL);

    ws.onopen = () => {
        console.log('Connected to server');
        reconnectAttempts = 0;
        console.log(`getting racer metadata for raceId: ${raceId}`)
        ws.send(JSON.stringify({ type : 'raceId', raceId : raceId }))
        currentRaceId = raceId
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message: ', data);

            switch (data.type) {
                case 'raceUpdate':
                    // Keep the original player_id format - no need to modify it
                    const formattedPositions = data.positions.map(p => ({
                        id: "P" + p.player_id,           // Keep as "P1", "P2", etc.
                        position: p.position,
                        coins: p.coins || 0,
                        item1: p.item_1,
                        item2: p.item_2
                    }));
                    console.log('Formatted positions:', JSON.stringify(formattedPositions));
                    raceTracker.updatePositions(formattedPositions);
                    break;

                case 'racerMetadata':
                    console.log('Racer metadata:', JSON.stringify(data.metadata))
                    setRacers(data.metadata)
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
                connectWebSocket(raceId);
            }, RECONNECT_DELAY);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function setRacers(racer_metadata) {
    const characterMap = new Map()

    for (const i in racer_metadata) {
        const racer = racer_metadata[i]
        console.debug('racer: ', JSON.stringify(racer))
        console.debug('player_id: ', `P${(racer.device_id * 2) + racer.device_player_num}`)
        console.debug('character: ', racer.character)

        characterMap.set(`P${(racer.device_id * 2) + racer.device_player_num}`, `${racer.character}`)
    }
    raceTracker.characterMap = characterMap
    // log character Map
    console.debug('characterMap: ', characterMap)
}

export function startRace(raceId) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWebSocket(raceId);
    }
}

export function stopRace() {
    if (ws) {
        ws.close();
    }
}

// Initialize race tracker and controls when they're mounted in React
export function initializeRaceTracker(containerId) {
    // Clean up existing tracker if it exists
    if (raceTracker) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    }

    raceTracker = new RaceTracker(containerId, {
        width: 1200,
        height: 800,
        margin: { top: 40, right: 40, bottom: 40, left: 40 },
        circleRadius: 32,
        circleSpacing: 72,
        timeWindowSize: 10
    });
    return raceTracker;
}

export function initializeControls(containerId) {
    // Clean up existing controls if they exist
    if (controls) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    }

    controls = new RaceControls(
        containerId,
        startRace,
        stopRace,
    );
    return controls;
}