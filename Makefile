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
	python src/pyscrape.py

scg:
	python src/g-scanner.py

scc:
	python src/c-scanner.py

scx:
	python src/x-scanner.py

ipc:
	python src/ip-check.py

pc:
	python src/picker.py

cmt:
	python src/remove.py

spg:
	python src/g-speed.py

spc:
	python src/c-speed.py

tb:
	python pytube.py

tg:
	python gemini.py

app:
	python app/app.py

py:
	. venv/bin/activate.fish; exec fish

burn:
	pip freeze > requirements.txt
