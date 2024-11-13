// main.js
import { RaceTracker } from './raceTracker.js';
import { RaceControls } from './controls.js';

let raceTracker;
let controls;
let currentRaceId;
let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

function connectWebSocket(raceId) {
    ws = new WebSocket('ws://localhost:3000');
    // ws = new WebSocket('ws://172.23.147.49:3000');

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
            // console.log('Received message: ', data);

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
                    console.log(JSON.stringify(data.metadata))
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
        console.debug(JSON.stringify(racer))
        console.debug(`P${racer.player_id}`)
        console.debug(racer.character)

        characterMap.set(`P${racer.player_id}`, `${racer.character}`)
    }
    raceTracker.characterMap = characterMap
}

function startRace(raceId) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWebSocket(raceId);
    }
}

function stopRace() {
    if (ws) {
        ws.close();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    raceTracker = new RaceTracker('race-tracker', {
        width: 400,
        height: 700,
        margin: { top: 20, right: 20, bottom: 20, left: 20 },
        circleRadius: 32,
        circleSpacing: 72
    });

    controls = new RaceControls(
        'controls',
        startRace,
        stopRace,
    );
});