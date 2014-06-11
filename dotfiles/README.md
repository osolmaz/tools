#nrs/dotfiles
#####My humble little collection of config files for the tools I use and love <3

* I use both ``vim`` and ``emacs``. ``emacs`` was my first editor, until I discovered the
modality vim provides. Now I use emacs only for ``Python`` and ``TeX``; and 
``vim`` is my default option for everything else.
* I tried out most of the distros (and I still do), and as an engineer dealing with
numerical computations, I find Arch Linux to be the most suited one for programming
with the rolling release aspect and its dynamic community.
* I like my tools to be fast, robust and efficient. I use the ``urxvt`` daemon for my
terminals, plus some perl scripts for convenience. 
* As a file manager, I use pcmanfm.
* Everybody has a favourite typeface when programming. Mine is specifically
``Dejavu Sans Mono``. I love the clarity and sharpness. It prevents
my eyes from going lazy, and keeps me awake without getting me tired. I have tried to
find alternatives in the past, but it is simply perfect. I've been using it almost
since I started programming.

##Installation
For a quick installation on an unconfigured system, just run ``make install``
in the main directory of the repository. *BEWARE* that this overwrites the
existing files.

Running this will copy all the dotfiles to the corresponding directories. The 
other recipe in the makefile ``copy`` is intended for me, which makes it easier
for me to update the repository.

##i3
Defines my daily experience with my computer. Modifications every now and then.

Useful features include automatic segregation of programs into different workspaces;
for example browsers into first, and pcmanfm desktop into last one. Despite my
previous thrash talk on solarized, I use solarized colors, just because they look 
so nice and contrasty. 

##vim
Built-up spending many hours searching the internet for vim tips and tricks. Uses
vundle for plugin management 

##emacs
Big stuff coming along. Writing plaintext is where this giant wins the game for me.
With AUCTeX, I am simply too lazy to learn the vim way of TeXing. Just firing up xdvik
with that auto-read option and binding keys to dvi compiling, you are ready for
hours of TeXing.

##bash
Just a boilerplate bash configuration. Nothing special

##zsh
With oh-my-zsh, I have all I need for a highly configured shell. 

##X
Nothing special with the ``.xinitrc`` file. But ``.Xdefaults`` has some settings for
urxvt.

##conky
Cool stuff
