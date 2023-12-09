.PHONY: test
run:
	@poetry run python wiki_bot.py

.PHONY: test
test:
	@poetry run python -m coverage run -m unittest
	@poetry run python -m coverage xml
	@rm -f .coverage
