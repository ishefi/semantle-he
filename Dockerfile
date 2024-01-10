#
FROM --platform=linux/amd64 python:3.11
#
ARG YAML_CONFIG_STR
ENV YAML_CONFIG_STR=${YAML_CONFIG_STR}
#
WORKDIR /code
#
COPY poetry.lock pyproject.toml /code/

#
RUN pip install --no-cache-dir --upgrade poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev
#

COPY ./common /code/common
COPY ./static /code/static
COPY ./templates /code/templates
COPY ./logic/ /code/logic
COPY ./routers/ /code/routers
COPY ./*.py /code

RUN python /code/download_model.py
COPY ./model.mdl* /code

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

