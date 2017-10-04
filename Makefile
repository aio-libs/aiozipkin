# Some simple testing tasks (sorry, UNIX only).

FLAGS=


flake: checkrst
	flake8 aiozipkin tests examples setup.py demos

test: flake
	py.test -s -v $(FLAGS) ./tests/

vtest:
	py.test -s -v $(FLAGS) ./tests/

checkrst:
	python setup.py check --restructuredtext

testloop:
	while true ; do \
        py.test -s -v $(FLAGS) ./tests/ ; \
    done

cov cover coverage: flake checkrst
	py.test -s -v --cov-report term --cov-report html --cov aiozipkin ./tests
	@echo "open file://`pwd`/htmlcov/index.html"

ci: flake
	py.test -s -v  --cov-report term --cov aiozipkin ./tests
	npm run eslint

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
	docker run -d --rm  –name zipkin -p 9411:9411 openzipkin/zipkin

zipkin_stop:
	docker stop zipkin

doc:
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"

.PHONY: all flake test vtest cov clean doc ci
