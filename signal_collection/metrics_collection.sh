#!/bin/bash

# Loop to capture the ps aux output every 1 seconds
while true; do
  echo "Snapshot at $(date)"
  ps -eo user,pid,ppid,%cpu,%mem,vsz,rss,tty,stat,start,time,command
  sleep 1
done