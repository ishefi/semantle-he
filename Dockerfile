#
FROM python:3.9
#
WORKDIR /code
#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
#
COPY ./common /code/common
COPY ./static /code/static
COPY ./templates /code/templates
COPY ./*.py /code
COPY ./config.yaml /code
COPY ./model.mdl* /code

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

