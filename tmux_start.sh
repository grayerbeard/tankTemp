#!/bin/bash
cd /home/pi/tankTemp
echo looking to kill any old tmux tank session
tmux kill-session -t tank
echo now new tmux tank session 
tmux new-session -d -s tank 'python3 tankTemp.py'
echo tmux session has been started    Press Enter 
exit 0
