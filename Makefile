# Some simple testing tasks (sorry, UNIX only).

FLAGS=

FILES := aiozipkin tests setup.py examples

fmt:
ifdef CI_LINT_RUN
	pre-commit run --all-files --show-diff-on-failure
else
	pre-commit run --all-files
endif

lint: bandit fmt
	mypy --show-error-codes --strict $(FILES)

test:
	py.test -s -v $(FLAGS) ./tests/

vtest:
	py.test -s -v $(FLAGS) ./tests/

checkrst:
	python setup.py check --restructuredtext

bandit:
	bandit -r ./aiozipkin

pyroma:
	pyroma -d .

testloop:
	while true ; do \
        py.test -s -v $(FLAGS) ./tests/ ; \
    done

cov cover coverage: flake checkrst
	py.test -s -v --cov-report term --cov-report html --cov aiozipkin ./tests
	@echo "open file://`pwd`/htmlcov/index.html"


clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf htmlcov
	rm -rf dist
	rm -rf node_modules

docker_clean:
	-@docker rmi $$(docker images -q --filter "dangling=true")
	-@docker rm $$(docker ps -q -f status=exited)
	-@docker volume ls -qf dangling=true | xargs -r docker volume rm

zipkin_start:
	docker run --name zipkin -d --rm  -p 9411:9411 openzipkin/zipkin:2

zipkin_stop:
	docker stop zipkin

doc:
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"


setup init:
	pip install -r requirements-dev.txt -r requirements-doc.txt
	pre-commit install

.PHONY: all flake test vtest cov clean doc ci
