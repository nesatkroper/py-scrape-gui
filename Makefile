git:
	git add . 
	git commit -m 'modified nun' 
	git push

clear: 
	find . -name "*.pyc" -delete 
	find . -name "__pycache__" -type d -exec rm -rf {} +

i: 
	pip install -r requirements.txt

ts:
	python pyscrape.py

tb:
	python pytube.py

tg:
	python gemini.py

py:
	. venv/bin/activate.fish; exec fish

burn:
	pip freeze > requirements.txt
