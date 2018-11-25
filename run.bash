#!/bin/bash

redis-server &
python3 worker.py &
python3 server.py
/bin/bash
