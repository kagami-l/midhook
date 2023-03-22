checkfiles = midhook tests

run-dev:
	@uvicorn midhook.app.app:app --reload --host 0.0.0.0 --port 12345

run-prod:
	@gunicorn midhook.app.app:app --workers 16 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:12345 --timeout 2400

check:
	@black --check $(checkfiles)
	@ruff check $(checkfiles) --fix

style:
	@isort -src $(checkfiles)
	@black $(checkfiles)