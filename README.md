# Hebrew Semantle
A Hebrew version of [Semantle](https://semantle.com/).

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


## Installation

Extract word2vec model in repository.
you can download one by following the instructions [here](https://github.com/Iddoyadlin/hebrew-w2v).

### Console 

```commandline
pip install poetry
poetry install
```

Install [mongodb](https://www.mongodb.com/docs/manual/installation/) and [redis](https://redis.io/docs/getting-started/installation/).

### Docker Compose
install Docker Compose from [here](https://docs.docker.com/compose/install/)

build the game with: 
```commandline
docker build compose
```

## Configuring databases
populate mongodb with vectors from word2vec model by running `populate.py` (make sure mongo db is running).
select secret word by running `set_secret.py` (make sure redis and mongo are running).

## Running the game

configurations should be set by creating a config.yaml file with the relevant settings (see config.format.yaml).
when running with docker compose, every change to configuration requires rebuilding.

### Console

You can run the game with:
```commandline
python app.py
```

you should run and configure mongo and redis server (see "Configuring Databases" section).
Word2Vec model was trained as described [here](https://github.com/Iddoyadlin/hebrew-w2v)

### Docker Compose

run the game with:
```commandline
docker build up
```

## Scripts

There are some useful scripts in the `scripts/` folder:

- `populate.py`: Given a Word2Vec model, will populate mongo collection used by the game.
- `set_secret.py`: Well...
- `semantle.py`: A CLI version of the game.

## Tests

Only for some of the logic right now. Sorry.

