all:
	@echo Run \'make install\' to install the config files to your system.

install: install-vimrc install-emacsd install-i3 install-bashrc install-zshrc install-conkyrc install-Xresources install-urxvt-perls install-terminator

install-emacsd:
	git submodule update --init --recursive
	cp -f .emacs.d ~/.emacs.d

install-vimrc:
	cp -f .vimrc ~/.vimrc
	git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
	vim +PluginInstall +qall

install-i3:
	mkdir -p ~/.i3
	cp .i3/config ~/.i3/config
	cp .i3/i3status.conf ~/.i3/i3status.conf

install-bashrc:
	cp -f .bashrc ~/.bashrc

install-zshrc:
	cp -f .zshrc ~/.zshrc

install-conkyrc:
	cp -f .conkyrc ~/.conkyrc

install-Xresources:
	cp -f .Xresources ~/.Xresources

install-urxvt-perls:
	cp -rf .urxvt-perls ~/.urxvt-perls

install-terminator:
	cp -f .config/terminator/config ~/.config/terminator/config

copy:
<<<<<<< HEAD
	cp -f ~/.vimrc vimrc
	mkdir -p i3
	cp -f ~/.i3/config i3/config
	cp -f ~/.i3/i3status.conf i3/i3status.conf
	cp -f ~/.Xresources Xresources
	cp -f ~/.bashrc bashrc
	cp -f ~/.zshrc zshrc
	cp -f ~/.conkyrc conkyrc
	cp -f ~/.xinitrc xinitrc
=======
	cp -f ~/.vimrc .vimrc
	mkdir -p .i3
	mkdir -p .config
	cp -f ~/.i3/config .i3/config
	cp -f ~/.i3/i3status.conf .i3/i3status.conf
	cp -f ~/.Xresources .Xresources
	cp -f ~/.bashrc .bashrc
	cp -f ~/.zshrc .zshrc
	cp -f ~/.conkyrc .conkyrc
	cp -f ~/.xinitrc .xinitrc
	mkdir -p .config/terminator/
	cp -f ~/.config/terminator/config .config/terminator/config
>>>>>>> 455465d (Minor)
