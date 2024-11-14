# MarioKart8CV
A project to take in MarioKart 8 videos and generate race stats using computer vision

# Development Setup
## Ubuntu/Debian

## macOS

## Windows
```powershell
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

```

# Dependencies
## Ubuntu/Debian
```
sudo apt-get update
sudo apt-get install redis-server
```

## macOS
```
brew install redis
```

## Windows
Download the Redis installer from https://github.com/microsoftarchive/redis/releases

# Setup
## Ubuntu/Debian
```
sudo systemctl start redis-server
source .venv/bin/activate
python ./mk8cv/main.py --resolution 1920x1080 --threads 1 --queue-size 1000 --num-devices 1 --frame-skip 8 --race-id 1
python ./mk8cv/aggregator/aggregator.py
cd ./mk8cv-viz
npm install
node server.js
```

## macOS
```
brew services start redis
source .venv/bin/activate
python ./mk8cv/main.py --resolution 1920x1080 --threads 1 --queue-size 1000 --num-devices 1 --frame-skip 8 --race-id 1
python ./mk8cv/aggregator/aggregator.py
cd ./mk8cv-viz
npm install
node server.js
```

## Windows
Run `redis-server.exe` from the installation directory
```
source .venv\Scripts\activate
python .\mk8cv\main.py --resolution 1920x1080 --threads 1 --queue-size 1000 --num-devices 1 --frame-skip 8 --race-id 1
python .\mk8cv\aggregator\aggregator.py
cd .\mk8cv-viz
npm install
node server.js
```


# Troubleshooting
```
redis-cli ping
```