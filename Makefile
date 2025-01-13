PY ?= python3

.PHONY: build test test-c test-js
build:
	@true

test-c:
	@true

test-js:
	node --test "frontend/tests/*.test.js"

test:
	$(PY) manage.py test tests --settings=pulsehub.settings.test --noinput
	$(MAKE) test-js
