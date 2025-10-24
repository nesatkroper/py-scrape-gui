DEX_PYTHON = .venv/bin/python

git:
	git add . 
	git commit -m 'modified nun' 
	git push
	git push nun

clear: 
	rm -rf venv
	rm -rf ~/.cache/pip
	python3 -m venv venv
	source venv/bin/activate.fish

dev:
	python src/app/app.py

i: 
	pip install -r requirements.txt

py:
	. venv/bin/activate.fish; exec fish

burn:
	pip freeze > requirements.txt
