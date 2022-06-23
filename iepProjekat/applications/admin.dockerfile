FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications

COPY admin/adminApp.py adminApp.py
COPY admin/adminDecorator.py adminDecorator.py
COPY configuration.py configuration.py
COPY models.py models.py
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "adminApp.py"]