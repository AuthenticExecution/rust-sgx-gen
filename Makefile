PWD                = $(shell pwd)
PYPI_REPO         ?= gianlu33/pypi
PYPI_USERNAME     ?= __token__
PYPI_PASSWORD     ?=

create_pkg:
	docker run --rm -v $(PWD):/usr/src/app $(PYPI_REPO) python setup.py sdist bdist_wheel

upload: create_pkg
	docker run --rm -v $(PWD):/usr/src/app $(PYPI_REPO) twine upload --repository pypi dist/* -u $(PYPI_USERNAME) -p $(PYPI_PASSWORD)

clean:
	sudo rm -rf dist/*
