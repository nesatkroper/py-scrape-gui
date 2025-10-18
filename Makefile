DEX_PYTHON = .venv/bin/python

git:
	git add . 
	git commit -m 'modified nun' 
	git push

clear: 
	rm -rf venv
	rm -rf ~/.cache/pip
	python3 -m venv venv
	source venv/bin/activate.fish


# 	find . -name "*.pyc" -delete 
# 	find . -name "__pycache__" -type d -exec rm -rf {} +

i: 
	pip install -r requirements.txt

# SCRAPE
ts:
	python src/pyscrape.py

# SCAN
scg:
	python src/g-scanner.py

scc:
	python src/c-scanner.py

scx:
	python src/x-scanner.py

# MEDIA
deg:
	python src/g-media.py

dec:
	python src/c-media.py

dex:
  $(DEX_PYTHON) src/x-media.py


# dex:
# 	python src/x-media.py

# IP CHECK
ipc:
	python src/ip-check.py

# PICKER
pc:
	python src/picker.py

# REMOVE
cmt:
	python src/remove.py

# SPEED
spg:
	python src/g-speed.py

spc:
	python src/c-speed.py

# PYTUBE
tb:
	python pytube.py

# OTHER
tg:
	python gemini.py

app:
	python app/app.py

py:
	. venv/bin/activate.fish; exec fish

burn:
	pip freeze > requirements.txt
