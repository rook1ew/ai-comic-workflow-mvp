.PHONY: run test lint

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	python -m compileall app
