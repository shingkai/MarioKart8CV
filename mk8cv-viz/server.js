const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const WebSocket = require('ws');
const http = require('http');
const cors = require('cors');
const path = require('path');

// Express setup
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Connect to SQLite database
const db = new sqlite3.Database('../mk8cv.db', (err) => {
    if (err) {
        console.error('Error connecting to database:', err);
    } else {
        console.log('Connected to SQLite database');
    }
});

// Track connected clients
const clients = new Set();

// WebSocket connection handler
wss.on('connection', (ws) => {
    console.log('New client connected');
    clients.add(ws);

    // Send initial race data
    sendActiveRaceData(ws);

    ws.on('close', () => {
        console.log('Client disconnected');
        clients.delete(ws);
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// Function to send race data to a specific client
async function sendActiveRaceData(ws) {
    try {
        // Get active race
        db.get(`
            SELECT DISTINCT race_id 
            FROM race_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        `, [], (err, raceRow) => {
            if (err || !raceRow) {
                ws.send(JSON.stringify({ type: 'error', message: 'No active race' }));
                return;
            }

            // Get latest positions for active race
            db.all(`
                WITH LatestTimestamps AS (
                    SELECT player_id, MAX(timestamp) as max_timestamp
                    FROM race_data
                    WHERE race_id = ?
                    GROUP BY player_id
                )
                SELECT rd.player_id, rd.position, rd.coins, rd.item_1, rd.item_2
                FROM race_data rd
                INNER JOIN LatestTimestamps lt 
                    ON rd.player_id = lt.player_id 
                    AND rd.timestamp = lt.max_timestamp
                WHERE rd.race_id = ?
                ORDER BY rd.position
            `, [raceRow.race_id, raceRow.race_id], (err, positions) => {
                if (err) {
                    ws.send(JSON.stringify({ type: 'error', message: err.message }));
                    return;
                }

                ws.send(JSON.stringify({
                    type: 'raceUpdate',
                    raceId: raceRow.race_id,
                    positions: positions
                }));
            });
        });
    } catch (error) {
        console.error('Error sending race data:', error);
    }
}

// Function to broadcast updates to all connected clients
function broadcastRaceUpdate(raceId) {
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            sendActiveRaceData(client);
        }
    });
}

// API endpoint to receive updates from your computer vision system
app.post('/api/racer-update', (req, res) => {
    const { raceId, timestamp, playerId, position, lap, coins, item1, item2 } = req.body;

    // Insert the new racer update
    db.run(`
        INSERT INTO race_data (race_id, timestamp, player_id, lap, position, coins, item_1, item_2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `, [raceId, timestamp, playerId, lap, position, coins || 0, item1 || 'None', item2 || 'None'],
    (err) => {
        if (err) {
            console.error('Error inserting race data:', err);
            res.status(500).json({ error: err.message });
            return;
        } else {
            console.log(`Received update: ${playerId} is in position ${position} with ${coins} coins`);
        }

        // Broadcast update to all connected clients
        broadcastRaceUpdate(raceId);
        res.json({ success: true });
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});