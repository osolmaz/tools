# For urxvt, use the clipboard script for copy-paste functionality (from the github repo below)

all:
	@echo Run \'make install\' to install the config files to your system.

install: install-vimrc install-emacsd install-i3 install-bashrc install-zshrc install-conkyrc install-Xresources

install-emacsd:
	git submodule update --init --recursive
	cp -f emacs.d ~/.emacs.d

install-vimrc:
	cp -f vimrc ~/.vimrc
	git clone https://github.com/gmarik/vundle.git ~/.vim/bundle/vundle
	vim +BundleInstall +qall

install-i3:
	mkdir -p ~/.i3
	cp i3/config ~/.i3/config
	cp i3/i3status.conf ~/.i3/i3status.conf

install-bashrc:
	cp -f bashrc ~/.bashrc

install-zshrc:
	cp -f zshrc ~/.zshrc

install-conkyrc:
	cp -f conkyrc ~/.conkyrc

install-Xresources:
	cp -f Xresources ~/.Xresources

urxvt-perl:
	git clone https://github.com/muennich/urxvt-perls

copy:
	cp -f ~/.vimrc vimrc
	mkdir -p i3
	cp -f ~/.i3/config i3/config
	cp -f ~/.i3/i3status.conf i3/i3status.conf
	cp -f ~/.Xresources Xresources
	cp -f ~/.bashrc bashrc
	cp -f ~/.zshrc zshrc
	cp -f ~/.conkyrc conkyrc
	cp -f ~/.xinitrc xinitrc

