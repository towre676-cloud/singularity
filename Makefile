.PHONY: test examples book release check handoff-check handoff-package

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

examples:
	PYTHONPATH=src python scripts/reproduce.py

book:
	python scripts/build_documents.py

check: test examples
	python scripts/check_repository.py

release: check book
	python scripts/package_release.py

handoff-check:
	python scripts/handoff.py verify

handoff-package:
	python scripts/handoff.py package
