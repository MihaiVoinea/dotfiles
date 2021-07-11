#
# ~/.bash_profile
#

[[ -f ~/.bashrc ]] && . ~/.bashrc

export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/ssh-agent.socket"

if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then sleep .25 && exec startx; fi
