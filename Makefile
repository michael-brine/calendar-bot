init:
	python3 -m venv env
	. ./env/bin/activate && python3 -m pip install -r requirements.txt
run: 
	. ./env/bin/activate && uvicorn main:app --reload
test:
	. ./env/bin/activate && python3 app/ai/chatbot.py
