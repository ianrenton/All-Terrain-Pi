#!/bin/bash
cd /home/pi/mjpg-streamer-experimental
export LD_LIBRARY_PATH=.
./mjpg_streamer -o "output_http.so -w ./www" -i "input_raspicam.so -fps 10 -x 320 -y 240 -vf -hf"
