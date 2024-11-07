// main.js
import { RaceTracker } from './raceTracker.js';
import { RaceControls } from './controls.js';

let raceTracker;
let controls;
let ws;
let currentRaceId = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:3000');
    // ws = new WebSocket('ws://172.23.147.49:3000');

    ws.onopen = () => {
        console.log('Connected to server');
        reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            // console.log('Received message: ', data);

            switch (data.type) {
                case 'raceUpdate':
                    currentRaceId = data.raceId;
                    // Keep the original player_id format - no need to modify it
                    const formattedPositions = data.positions.map(p => ({
                        id: p.player_id,           // Keep as "P1", "P2", etc.
                        position: p.position,
                        coins: p.coins || 0,
                        item1: p.item_1,
                        item2: p.item_2
                    }));
                    // console.log('Formatted positions:', formattedPositions);
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