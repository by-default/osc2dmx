#!/usr/bin/env bash

mkdir -p build/opt/osc2dmx
mkdir -p build/etc/systemd/system
cp main.py build/opt/osc2dmx/
cp settings.py.example build/opt/osc2dmx/
cp osc2dmx.service build/etc/systemd/system
chmod +x build/opt/osc2dmx/main.py
