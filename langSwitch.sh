#!/usr/bin/env bash

sudo rm -r /usr/share/snips/assistant
sudo cp -r ./assistants/assistant_"$1" /usr/share/snips/assistant
sudo systemctl restart "snips*"
sleep 1