venv: clean
	python3.10 -m venv venv

clean:
	rm -rf venv

install: venv
	bash -c "source venv/bin/activate; pip install -r requirements.txt;"

