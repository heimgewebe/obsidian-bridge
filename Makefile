.PHONY: test lint clean install install-deps

test:
	bats tests/*.bats
	python3 -m unittest discover -s tests -p 'test_*.py'

lint:
	bash -c 'find bin scripts -type f -print0 | while IFS= read -r -d "" f; do if file --brief --mime-type -- "$$f" | grep -q "text/x-shellscript"; then shellcheck -- "$$f"; fi; done'
	find scripts -type f -name "*.py" -print0 | xargs -0 -r python3 -m py_compile

clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install-deps:
	python3 -m pip install -r requirements.txt

install: install-deps
	@echo "Symlinking tools to ~/.local/bin..."
	mkdir -p ~/.local/bin
	ln -sf $$(pwd)/bin/obsidian-clean ~/.local/bin/obsidian-clean
	ln -sf $$(pwd)/bin/obsidian-json ~/.local/bin/obsidian-json
	ln -sf $$(pwd)/bin/obsidian-env ~/.local/bin/obsidian-env
	ln -sf $$(pwd)/bin/obsidian-doctor ~/.local/bin/obsidian-doctor
	@echo "Done!"
