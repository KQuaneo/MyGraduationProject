#!/bin/sh

sleep 2

for _ in 1 2 3 4 5; do
    if ! xrandr --query >/dev/null 2>&1; then
        sleep 1
        continue
    fi

    if xrandr --query | grep -q '^HDMI-1 connected'; then
        xrandr --output HDMI-1 --mode 1024x600 --rate 59.82 --primary && exit 0
        xrandr --output HDMI-1 --auto --primary && exit 0
    fi

    sleep 1
done

exit 0
