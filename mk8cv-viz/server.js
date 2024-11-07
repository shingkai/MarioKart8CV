const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const cors = require('cors');
const path = require('path');

// Enable CORS for your frontend
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

// Endpoint to get latest positions for a specific race
app.get('/api/positions/:raceId', (req, res) => {
    const { raceId } = req.params;

    // Get the most recent timestamp for this race
    db.get(`
        SELECT MAX(timestamp) as latest_timestamp 
        FROM race_positions 
        WHERE race_id = ?
    `, [raceId], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }

        if (!row.latest_timestamp) {
            res.json([]);
            return;
        }

        // Get all positions for this timestamp
        db.all(`
            SELECT player_id, position 
            FROM race_positions 
            WHERE race_id = ? AND timestamp = ?
            ORDER BY position
        `, [raceId, row.latest_timestamp], (err, positions) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.json(positions);
        });
    });
});

// Endpoint to get active race ID
app.get('/api/active-race', (req, res) => {
    db.get(`
        SELECT DISTINCT race_id 
        FROM race_positions 
        ORDER BY timestamp DESC 
        LIMIT 1
    `, [], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        res.json({ raceId: row ? row.race_id : null });
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
