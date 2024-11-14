const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const WebSocket = require('ws');
const http = require('http');
const cors = require('cors');
const path = require('path');
const fs = require("node:fs");

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

    let raceId = undefined

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)

            switch(data.type) {
                case 'raceId':
                    console.log(`New client requesting raceId: ${data.raceId}`)
                    // Send Racer Metadata
                    sendRacerMetadata(ws, data.raceId)
                    raceId = data.raceId
                    // Periodically send race data
                    autoUpdateClient(ws, data.raceId)
                    break;
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    }


    ws.on('close', () => {
        console.log('Client disconnected');
        clients.delete(ws);
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// TODO: figure out a better way to do this -- make sure the interval is terminated if ws is disconnected
async function autoUpdateClient(ws, raceId) {
    setInterval(async () => {
        console.debug(`sending race data for ${raceId}`)
        sendActiveRaceData(ws, raceId)
    }, 1000); // send every 1000 ms
}

async function sendRacerMetadata(ws, raceId) {
    try {
        console.debug(`fetching racer metadata`)
        db.all('SELECT * from racer_metadata;', (err, racerMetadata) => {
            if (err || !racerMetadata) {
                console.error(racerMetadata)
                ws.send(JSON.stringify({ type: 'error', message: `Error fetching racer metadata: ${err.message}` }));
                return;
            }
            console.log(`sending ${JSON.stringify(racerMetadata)}`)
            ws.send(JSON.stringify({ type:'racerMetadata', metadata: racerMetadata }));
        });
    } catch (error) {
        console.error('Error sending race data:', error);
    }
}

// Function to send race data to a specific client
async function sendActiveRaceData(ws, raceId) {
    console.log(`sending race update for raceId: ${raceId}`)
    try {
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
        `, [raceId, raceId], (err, positions) => {
            if (err) {
                ws.send(JSON.stringify({ type: 'error', message: err.message }));
                return;
            }
            console.debug(`sending: ${JSON.stringify({
                type: 'raceUpdate',
                raceId: raceId,
                positions: positions
            })}`)
            ws.send(JSON.stringify({
                type: 'raceUpdate',
                raceId: raceId,
                positions: positions
            }));
        });
    } catch (error) {
        console.error('Error sending race data:', error);
    }
}

// Function to broadcast updates to all connected clients
// TODO: we probably need to maintain a map of client -> raceId
function broadcastRaceUpdate(raceId) {
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            sendActiveRaceData(client, raceId);
        }
    });
}

// API endpoint to receive updates from your computer vision system
app.post('/api/racer-update', (req, res) => {
    console.debug('call to /api/racer-update')
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

app.get('/api/racer-metadata', (req, res) => {
    console.log('Fetching racer metadata');

    db.all('SELECT * FROM racer_metadata', (err, rows) => {
        if (err) {
            console.error('Error fetching racer metadata:', err);
            res.status(500).json({ error: err.message });
            return;
        }
        console.log('Racer metadata:', rows);
        res.json(rows);
    });
});

// Add or update racer metadata
app.post('/api/racer-metadata', (req, res) => {
    console.log('Saving racer metadata:', req.body);
    const { deviceId, player1Name, player1Character, player2Name, player2Character } = req.body;

    // Calculate player IDs
    const player1Id = deviceId * 2;
    const player2Id = deviceId * 2 + 1;

    // Use a transaction to insert both players
    db.serialize(() => {
        db.run('BEGIN TRANSACTION');

        try {
            // Insert or update player 1
            db.run(`
                INSERT INTO racer_metadata (player_id, device_id, device_player_num, player_name, character)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(player_id) 
                DO UPDATE SET
                    device_id = excluded.device_id,
                    device_player_num = excluded.device_player_num,
                    player_name = excluded.player_name,
                    character = excluded.character
            `, [player1Id, deviceId, player1Name, player1Character]);

            // Insert or update player 2
            db.run(`
                INSERT INTO racer_metadata (player_id, device_id, device_player_num, player_name, character)
                VALUES (?, ?, 2, ?, ?)
                ON CONFLICT(player_id) 
                DO UPDATE SET
                    device_id = excluded.device_id,
                    device_player_num = excluded.device_player_num,
                    player_name = excluded.player_name,
                    character = excluded.character
            `, [player2Id, deviceId, player2Name, player2Character]);

            db.run('COMMIT');
            res.json({ success: true });
        } catch (error) {
            db.run('ROLLBACK');
            console.error('Error saving racer metadata:', error);
            res.status(500).json({ error: error.message });
        }
    });
});

app.get('/api/characters', async (req, res) => {
    try {
        const directoryPath = path.join(__dirname, './mario_kart_8_images/Character select icons');
        console.log('Reading characters directory:', directoryPath);
        const files = await fs.promises.readdir(directoryPath);
        const characters = files
            .filter(file => file.endsWith('.png'))
            .map(file => file.replace('.png', ''));
        res.json(characters);
    } catch (error) {
        console.error('Error reading characters directory:', error);
        res.status(500).json({ error: error.message });
    }
});


const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});