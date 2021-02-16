PWD 						= $(shell pwd)
PYPI_REPO				?= gianlu33/pypi
PYPI_USERNAME		?= __token__

create_pkg:
	docker run --rm -it -v $(PWD):/usr/src/app $(PYPI_REPO) python setup.py sdist bdist_wheel

upload: create_pkg
	docker run --rm -it -v $(PWD):/usr/src/app $(PYPI_REPO) twine upload --repository pypi dist/* -u $(PYPI_USERNAME)

clean:
	sudo rm -rf dist/*
