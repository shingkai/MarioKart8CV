# MarioKart8CV
A project to take in MarioKart 8 videos and generate race stats using computer vision

# 1. Install Redis
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

# 2. Start Redis server
## Ubuntu/Debian
```
sudo systemctl start redis-server
```

## macOS
```
brew services start redis
```

## Windows
Run redis-server.exe from the installation directory

# 3. Install Python Redis client
 ```
 pip install redis
```

# 4. Test Redis connection
```
redis-cli ping
```