#!/bin/bash

#source ~/python-environments/whisper-live/bin/activate

python3 run_server.py --host 127.0.0.1 --port 9090 --backend faster_whisper
