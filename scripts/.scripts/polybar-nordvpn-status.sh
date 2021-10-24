#!/bin/sh

STATUS=$(nordvpn status | grep Status | tr -d ' ' | cut -d ':' -f2)

if [ "$STATUS" = "Connected" ]; then
    echo "%{F#23d18b}%{A1:nordvpn d:} $(nordvpn status | grep City | cut -d ':' -f2)%{A}%{F-}"
else
    echo "%{F#f14c4c}%{A1:nordvpn c:} No VPN%{A}%{F-}"
fi
