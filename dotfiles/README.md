#nrs/dotfiles
#####a.k.a. Mechanician's Humble Config Collection

> My humble little collection of config files for the everyday
tools I use and love <3. See the following entries for more explanation.

This collection is a result of many hours of config refinement. I
enjoy spending many hours on this fine art of optimizing interfaces and my
productivity. For me, this is more than just a hobby, this is passion.
Hence this collection is ideal to look at for people who like simple, uncluttered
interfaces; who seek ways to type and click less to produce more. Of course,
there is no assertion of perfection and there shall not be, since that is not
the purpose. Elegance is sought to an ultimate level, if possible, and beneath 
that lies the zone of dirty hacks and nauseating workarounds.

As an engineer with some years of \*nix (mainly GNU/Linux) experience, I definitely
tried a lot of interfaces and editors in my free time. Some of my ongoing hobbies are
editing config files, reading manpages. Although regretting getting acquainted with
the world of free software a little bit late, I'm glad that it wasn't too late.
To this date, I have tested many interfaces and editors, and here are some highlights 
that will clarify my point of view on ways of programming.

* I use both ``vim`` and ``emacs``. ``emacs`` was my first sweetheart, until I discovered the
modality vim provides. Now I use emacs only for ``Python`` and ``TeX``; and 
``vim`` is my default option for everything else.
* I do not use IDEs. If you think that is better; well I've had enough arguments
regarding this issue. To me, IDEs are just in the way of achieving the abstract
and universal interface I seek when I program in multiple languages. I would rather
operate over simple text files than try to find my way through combinations of
mouse clicks, menus, dropdowns, and other contraptions.
* I tried out most of the distros (and I still do), and as an engineer dealing with
numerical computations, I find Arch Linux to be the most suited one for programming
with the rolling release aspect and its dynamic community. Not to mention that 
it is simple, elegant, and all the things I mentioned earlier.
* GNOME 2 was the greatest desktop environment of all time for me. I sat and cried 
when I saw what happened afterwards. Now MATE (its fork) carries the torch... thanks 
to an Arch Linux user.
* The first time I used a tiling window manager was after few months that I started
programming. I was using ``xmonad``. After some time, I realized that I was torturing
myself. When I saw ``i3`` for the first time, I was a bit skeptical. After a few videos,
I was convinced enough to install and spend time configuring this manager. It turned
out to be great. I now use ``i3`` for my daily computing, and non-computing i.e. the time 
spent watching Youtube videos. I borrow some of the system tools from MATE, because 
after all, there are some aspects you don't have time to configure and write scripts
from scratch.
* I use Firefox, end of line. Note that I'm not that into web development.
* I found ``zsh ``to be great for daily use, with its numerous features which makes
it superior to bash.
* I like my tools to be fast, robust and efficient. I use the ``urxvt`` daemon for my
terminals, plus some perl scripts for convenience. Also, not to forget one of my
indispensable allies, ``tilda``. This little fellow saved me so many keystrokes,
it is unbeliavable. 
* As a file manager, I use pcmanfm, as it complies with the criteria I previously
presented. I use it as the "Desktop" in ``i3``, since it doesn't provide one readily.
* Everybody has a favourite typeface when programming. Mine is specifically
``Dejavu Sans Mono``, sizes 9-12pt. I love the clarity and sharpness. It prevents
my eyes from going lazy, and keeps me awake without getting me tired. I have tried to
find alternatives in the past, but it is simply perfect. I've been using it almost
since I started programming.
* Color is also an issue when programming. People generally end up in pale and
harmonious colorschemes like solarized, defending its multi-purpose day versus
night interchangeability. But it simply makes me lazy, and I always use the same
colorscheme for my programming, namely the one given to me by a very good person
a long time ago. Characteristics 
include light gray text over a black background with conservative colors for
syntax highlighting such as red, light green, dark green, yellow, orange, 
cyan and so on. The ``vim`` version ``vim-forthran`` 
can be found among my github repositories. It is automatically added to vim via 
``vundle``. For emacs, it is already in the dotfile. 

##Installation
For a quick installation on an unconfigured system, just run ``make install``
in the main directory of the repository. BEWARE that this overwrites the
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
vundle for plugin management (vundle is just breathtakingly awesome, adds unmatched
plugin handling functionalities to vim. Suck on that, textmate and sublime). Basically,
this config defines how I create programs out of nothingness.

For more, please refer to the dotfile itself.

##emacs
Big stuff coming along. Writing plaintext is where this giant wins the game for me.
With AUCTeX, I am simply too lazy to learn the vim way of TeXing. Just firing up xdvik
with that auto-read option and binding keys to dvi compiling, you are ready for
hours of TeXing.

##bash
Just a boilerplate bash configuration. Nothing special... yet.

##zsh
With oh-my-zsh, I have all I need for a highly configured shell. Aside from that,
what more can a man ask for.

##X
Nothing special with the ``.xinitrc`` file. But ``.Xdefaults`` has some settings for
urxvt.

##conky
If you also own a mediocre laptop like myself, you should empathize with the problem
of low storage space, memory and overheating. This sucker helps me monitor how
shitty a computer I own. Modify as you like, since I customized it for my own
hardware. It is based on some examples I found online.
