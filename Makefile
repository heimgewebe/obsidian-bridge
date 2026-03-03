.PHONY: test lint clean install

test:
	bats tests/*.bats

lint:
	shellcheck bin/* scripts/*.sh

clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install:
	@echo "Symlinking tools to ~/.local/bin..."
	mkdir -p ~/.local/bin
	ln -sf $$(pwd)/bin/obsidian-clean ~/.local/bin/obsidian-clean
	ln -sf $$(pwd)/bin/obsidian-json ~/.local/bin/obsidian-json
	ln -sf $$(pwd)/bin/obsidian-env ~/.local/bin/obsidian-env
	ln -sf $$(pwd)/bin/obsidian-doctor ~/.local/bin/obsidian-doctor
	@echo "Done!"
