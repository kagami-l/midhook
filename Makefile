checkfiles = midhook tests

run-dev:
	@uvicorn midhook.app.app:app --reload --host 0.0.0.0 --port 23518

# run-prod:
# 	@gunicorn midhook.app.app:app --workers 16 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:12345 --timeout 2400

check:
	@black --check $(checkfiles)
	@ruff check $(checkfiles) --fix

style:
	@isort -src $(checkfiles)
	@black $(checkfiles)

build:
	@docker build -f ./devops/Dockerfile -t local/midhook:1 .

enter:
	@docker exec -it dk-hook bash

dk-run:
	@docker run -d --rm -p 12345:12345 --name dk-hook local/midhook:1 