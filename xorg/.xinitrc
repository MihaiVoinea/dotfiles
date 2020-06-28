[[ -f /usr/bin/numlockx ]] && numlockx

[[ -f ~/.Xresources ]] && xrdb -merge ~/.Xresources

[[ -f /usr/bin/i3 ]] && exec i3
