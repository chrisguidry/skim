.DEFAULT_GOAL := install

.bookkeeping/development.txt: .bookkeeping/pip-tools requirements.txt
	mkdir -p .bookkeeping
	cat requirements.txt > .bookkeeping/development.txt.next

	pip install -r .bookkeeping/development.txt.next
	pip-sync .bookkeeping/development.txt.next
	docker-compose build --pull

	mv .bookkeeping/development.txt.next .bookkeeping/development.txt

.bookkeeping/pip-tools:
	mkdir -p .bookkeeping
	touch .bookkeeping/pip-tools.next

	pip install -U pip pip-tools

	mv .bookkeeping/pip-tools.next .bookkeeping/pip-tools

%.txt: %.in .bookkeeping/pip-tools
	pip-compile --upgrade --output-file $@ $<

.PHONY: install
install: .bookkeeping/development.txt

.PHONY: clean
clean:
	rm -Rf .bookkeeping/
