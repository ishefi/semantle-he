#
FROM --platform=linux/amd64 python:3.12
#
ARG YAML_CONFIG_STR
ENV YAML_CONFIG_STR=${YAML_CONFIG_STR}
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

#
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

#
WORKDIR /code

#
COPY uv.lock pyproject.toml /code/

#
RUN pip install --no-cache-dir --upgrade uv==0.6.17
RUN uv sync --no-install-project --locked
RUN pip install setuptools
#

COPY ./common /code/common
COPY ./static /code/static
COPY ./templates /code/templates
COPY ./logic/ /code/logic
COPY ./routers/ /code/routers
COPY ./*.py /code

RUN python /code/download_model.py
RUN rm /code/model.zip

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

