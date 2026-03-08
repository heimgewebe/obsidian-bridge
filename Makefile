.PHONY: test lint clean install

test:
	bats tests/*.bats

lint:
	find bin scripts -type f -print0 | xargs -0 -r file | grep -E 'shell script|POSIX shell script' | cut -d: -f1 | tr '\n' '\0' | xargs -0 -r shellcheck
	find scripts -type f -name "*.py" -print0 | xargs -0 -r python3 -m py_compile

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
