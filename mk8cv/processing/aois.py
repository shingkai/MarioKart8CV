
from mk8cv.data.state import Player, Stat

CROP_COORDS = {
    Player.P1 : {
        Stat.POSITION: (0.38, 0.47, 0.84, 0.97),
        Stat.COINS: (0.056, 0.09, 0.92, 0.965),
        Stat.LAP_NUM: (0.121, 0.135, 0.925, 0.9635),
        Stat.RACE_LAPS: (0.146, 0.161, 0.925, 0.9635),
        Stat.ITEM1: (0.08, 0.164, 0.08, 0.23),
        Stat.ITEM2: (0.039, 0.082, 0.047, 0.13),
    },
    Player.P2 : {
        Stat.POSITION: (0.88, 0.97, 0.84, 0.97),
        Stat.COINS: (0.556, 0.59, 0.92, 0.965),
        Stat.LAP_NUM: (0.621, 0.635, 0.925, 0.9635),
        Stat.RACE_LAPS: (0.646, 0.661, 0.925, 0.9635),
        Stat.ITEM1: (0.834, 0.918, 0.08, 0.23),
        Stat.ITEM2: (0.915, 0.958, 0.047, 0.13),
    }
}