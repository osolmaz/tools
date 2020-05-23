# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
#ZSH_THEME="gozilla"
#ZSH_THEME="robbyrussell"
#ZSH_THEME="macovsky"
#ZSH_THEME="linuxonly"
#ZSH_THEME="af-magic"
#ZSH_THEME="agnoster"
ZSH_THEME="afowler"
# ZSH_THEME="ys"
# ZSH_THEME="smt"
# ZSH_THEME="bira"
# ZSH_THEME="bureau"
# ZSH_THEME="terminalparty"
# ZSH_THEME="Honukai"
#ZSH_THEME="amuse"
#ZSH_THEME="pygmalion"

# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Set to this to use case-sensitive completion
CASE_SENSITIVE="true"

# Comment this out to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment to change how many often would you like to wait before auto-updates occur? (in days)
# export UPDATE_ZSH_DAYS=13

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
COMPLETION_WAITING_DOTS="true"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(cp zsh-autosuggestions)

source $ZSH/oh-my-zsh.sh

#setopt autolist
#unsetopt menucomplete
setopt noautomenu
setopt extended_glob
setopt auto_cd
autoload zmv
setopt pushdsilent

#setopt auto_pushd
#setopt pushd_ignore_dups
#setopt pushdminus


# Customize to your needs...
# Some setting directly from bashrc


function rld (){
    source ~/.zshrc
}

function gmp {
    if [ ! -z $1 ]
    then
        git commit -a -m "$1";
    else
        git commit -a -m "Minor";
    fi
    git push;
}


function listbiggest(){
    du -a . | sort -r -n | head -n 10
}

function em() {
  (emacs "$@"&)
}

function paradise(){
    mplayer http://stream-dc1.radioparadise.com/aac-128
}

function md2pdf {
  pandoc "$1" -o "$(basename "$1" .md).pdf"
}


zstyle ':completion:*' special-dirs true

source ~/.bash_aliases
# source /etc/profile.d/fzf.zsh

set noclobber

