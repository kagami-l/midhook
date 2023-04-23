checkfiles = midhook tests

run-dev:
	@uvicorn midhook.app.app:app --reload --host 0.0.0.0 --port 23518

run-prod:
	@gunicorn midhook.app.app:app --workers 16 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:12345 --timeout 2400

check:
	@black --check $(checkfiles)
	@ruff check $(checkfiles) --fix

style:
	@isort -src $(checkfiles)
	@black $(checkfiles)

build:
	@docker build -f ./deploy/Dockerfile -t local/midhook:1 .

enter:
	@docker run -it --rm local/midhook:1 bash

dk-run:
	@docker run --rm -p 23518:23518 local/midhook:1