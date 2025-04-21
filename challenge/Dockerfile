FROM ubuntu
RUN apt update && apt install -y python3 python3-pip
WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt
RUN playwright install-deps
RUN playwright install

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]