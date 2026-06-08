.PHONY: gate record api web dev test

gate:
	python -m pytest tests/test_gate.py -q

test:
	python -m pytest -q

record:
	FORCE_MOCK=1 python -m engine.run --record

api:
	uvicorn transport.server:app --host 127.0.0.1 --port 8000 --reload

web:
	cd web && npm run dev

dev:
	@echo "Run API and web in separate terminals: make api / make web"
