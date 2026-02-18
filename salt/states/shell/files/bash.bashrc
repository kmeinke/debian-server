# System-wide bashrc — managed by Salt

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

# History
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoredups:erasedups
shopt -s histappend

# Prompt
if [ "$(id -u)" -eq 0 ]; then
  PS1='\[\e[1;31m\]\u@\h\[\e[0m\]:\[\e[1;34m\]\w\[\e[0m\]# '
  [ -f /etc/motd.root ] && cat /etc/motd.root
  echo "  Load     : $(cut -d' ' -f1-3 /proc/loadavg) (1/5/15 min)"
  echo
else
  PS1='\[\e[1;32m\]\u@\h\[\e[0m\]:\[\e[1;34m\]\w\[\e[0m\]$ '
fi

# Aliases
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'

# Enable bash completion
if [ -f /etc/bash_completion ]; then
  . /etc/bash_completion
fi
