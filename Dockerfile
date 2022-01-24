FROM python:3.9

WORKDIR /code

COPY src/requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

COPY secret/ /root/.config/gspread/

CMD ["python3", "./main.py"]
