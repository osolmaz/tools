all:
	@echo Run \'make install\' to install the config files to your system.

install: install-vimrc install-emacsd install-i3 install-bashrc install-zshrc install-conkyrc install-Xresources install-urxvt-perls install-terminator install-aerospace install-iterm2 install-ghostty install-cmux install-zed

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

install-Xresources:
	cp -f .Xresources ~/.Xresources

install-urxvt-perls:
	cp -rf .urxvt-perls ~/.urxvt-perls

install-terminator:
	cp -f .config/terminator/config ~/.config/terminator/config

install-aerospace:
	cp -f .aerospace.toml ~/.aerospace.toml

install-iterm2:
	./scripts/iterm2-prefs install

install-ghostty:
	mkdir -p "$$HOME/Library/Application Support/com.mitchellh.ghostty"
	cp -f "Library/Application Support/com.mitchellh.ghostty/config.ghostty" "$$HOME/Library/Application Support/com.mitchellh.ghostty/config.ghostty"

install-cmux:
	mkdir -p "$$HOME/.config/cmux"
	cp -f .config/cmux/cmux.json "$$HOME/.config/cmux/cmux.json"
	./scripts/cmux-prefs install

install-zed:
	mkdir -p ~/.config/zed
	cp -f .config/zed/settings.json ~/.config/zed/settings.json

copy:
	cp -f ~/.vimrc .vimrc
	mkdir -p .i3
	mkdir -p .config
	cp -f ~/.i3/config .i3/config
	cp -f ~/.i3/i3status.conf .i3/i3status.conf
	cp -f ~/.Xresources .Xresources
	cp -f ~/.bashrc .bashrc
	cp -f ~/.zshrc .zshrc
	cp -f ~/.xinitrc .xinitrc
	cp -f ~/.aerospace.toml .aerospace.toml
	./scripts/iterm2-prefs copy
	mkdir -p "Library/Application Support/com.mitchellh.ghostty"
	cp -f "$$HOME/Library/Application Support/com.mitchellh.ghostty/config.ghostty" "Library/Application Support/com.mitchellh.ghostty/config.ghostty"
	mkdir -p .config/cmux
	cp -f "$$HOME/.config/cmux/cmux.json" .config/cmux/cmux.json
	./scripts/cmux-prefs copy
	mkdir -p .config/terminator/
	cp -f ~/.config/terminator/config .config/terminator/config
	mkdir -p .config/zed/
	cp -f ~/.config/zed/settings.json .config/zed/settings.json
