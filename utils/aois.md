# Areas of Interest

## 2 Players

### 640 x 360 Absolute Coordinates  
Coordinates are based on a 640x360 scaled image.

| AOI      | Dimensions | P1 Base  | P2 Base  |
|----------|------------|----------|----------|
| 1st Item | 50 x 50    | 52 | 30   | 536 | 30  |
| 2nd Item | 25 x 25    | 26 | 20   | 586 | 20  |
| Place    | 50 x 50    | 240 | 300 | 560 | 300 |
| Coins    | 24 x 20    | 34 | 330  | 353 | 330 |
| Lap      | 32 x 20    | 72 | 330  | 391 | 330 |

### Relative Percentage Coordinates
Coordinates are based as a percentage of the total image. Values will need to be rounded | and may result in drift for smaller resolutions.

| AOI | x1 | x2 | y1 | y2 |
|-----|----|----|----|----|
| P1 1st Item | 0.08 | 0.164 | 0.08 | 0.23 |
| P2 1st Item | 0.834 | 0.918 | 0.08 | 0.23 |
| P1 2nd Item | 0.039 | 0.082 | 0.047 | 0.13 |
| P2 2nd Item | 0.915 | 0.958 | 0.047 | 0.13 |
| P1 Position | 0.38 | 0.47 | 0.84 | 0.97 |
| P2 Position | 0.88 | 0.97 | 0.84 | 0.97 |
| P1 Coins | 0.03 | 0.09 | 0.91 | 0.97 |
| P2 Coins | 0.53 | 0.59 | 0.91 | 0.97 |
| P1 Lap | 0.09 | 0.17 | 0.91 | 0.97 |
| P2 Lap | 0.59 | 0.67 | 0.91 | 0.97 |

## todo
- [ ] Handle switch per-tv resolution scaling (crop bounding box & scale?)
- [ ] figure out why capture only gets 30fps instead of 60