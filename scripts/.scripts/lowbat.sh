BATPATH=/sys/class/power_supply/BAT0
BAT_CAPACITY=$(cat $BATPATH/capacity)
if [ $(($BAT_CAPACITY)) -lt 20 ]
then
	    notify-send "Low battery!"
fi

if [ $(($BAT_CAPACITY)) -lt 5 ]
then
	    systemctl suspend
fi
