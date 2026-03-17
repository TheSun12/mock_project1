.PHONY: run test clean

run:
	flask --app app run --host 0.0.0.0 --port 8000

test:
	pytest tests/

clean:
	rm -f mock_cbr.db
