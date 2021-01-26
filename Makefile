SHELL:=/bin/bash

include .env

KEY = $(shell aws --profile wavelength configure get aws_access_key_id)
SECRET = $(shell aws --profile wavelength configure get aws_secret_access_key)
REGION = $(shell aws --profile wavelength configure get region)

.PHONY: clean creds
clean creds:
	make  -f Makefile.targets $(MAKECMDGOALS) $(MAKEFLAGS)

.PHONY: deps
deps:
	pip install -r ./test/requirements.txt && python setup.py develop


.PHONY: lint test unit-test integration-test check coverage build deploy deploy-overwrite
lint test unit-test integration-test check coverage build deploy deploy-overwrite:
	docker-compose run -e AWS_ACCESS_KEY_ID=${KEY} -e AWS_SECRET_ACCESS_KEY=${SECRET} -e AWS_DEFAULT_REGION=${REGION} --rm app make -f Makefile.targets $(MAKECMDGOALS) $(MAKEFLAGS)

