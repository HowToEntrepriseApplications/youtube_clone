FROM python:3.8.3-slim-buster

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIPENV_VENV_IN_PROJECT=1


RUN pip install --upgrade pip==20.1.1 && pip install pipenv==2020.6.2

WORKDIR /webapp
COPY Pipfile* /webapp/
RUN pipenv install --deploy --ignore-pipfile --dev

COPY . /webapp/
CMD ["pipenv", "run", "runserver"]