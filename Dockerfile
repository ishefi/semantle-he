#
FROM python:3.11
#
WORKDIR /code
#
COPY ./pyproject.toml /code/pyproject.toml
#
RUN pip install --no-cache-dir --upgrade poetry
RUN poetry install --no-dev
#

COPY ./common /code/common
COPY ./static /code/static
COPY ./templates /code/templates
COPY ./*.py /code
COPY ./config.yaml* /code

RUN python /code/download_model.py

COPY ./model.mdl* /code

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

