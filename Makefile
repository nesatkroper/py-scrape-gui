git:
	git add . 
	git commit -m 'modified nun' 
	git push

clear: 
	find . -name "*.pyc" -delete 
	find . -name "__pycache__" -type d -exec rm -rf {} +

i: 
	pip install -r requirements.txt

dev:
	python main.py

py:
	. venv/bin/activate.fish; exec fish

burn:
	pip freeze > requirements.txt
