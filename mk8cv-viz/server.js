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
const db = new sqlite3.Database('races.db', (err) => {
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
            FROM race_positions 
            ORDER BY timestamp DESC 
            LIMIT 1
        `, [], (err, raceRow) => {
            if (err || !raceRow) {
                ws.send(JSON.stringify({ type: 'error', message: 'No active race' }));
                return;
            }

            // Get positions for active race
            db.all(`
                SELECT player_id, position 
                FROM race_positions 
                WHERE race_id = ? 
                AND timestamp = (
                    SELECT MAX(timestamp) 
                    FROM race_positions 
                    WHERE race_id = ?
                )
                ORDER BY position
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
function broadcastRaceUpdate(raceId, positions) {
    const message = JSON.stringify({
        type: 'raceUpdate',
        raceId: raceId,
        positions: positions
    });

    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// API endpoint to receive updates from your computer vision system
app.post('/api/position-update', (req, res) => {
    const { raceId, positions, timestamp } = req.body;

    // Begin transaction
    db.serialize(() => {
        const stmt = db.prepare(`
            INSERT INTO race_positions (timestamp, player_id, position, race_id)
            VALUES (?, ?, ?, ?)
        `);

        positions.forEach(pos => {
            stmt.run(timestamp, pos.player_id, pos.position, raceId);
        });

        stmt.finalize((err) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            // Broadcast update to all connected clients
            broadcastRaceUpdate(raceId, positions);
            res.json({ success: true });
        });
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});