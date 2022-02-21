# Hebrew Semantle
A Hebrew version of [Semantle](https://semantle-he.herokuapp.com/).

## Installation
Just like any Python project: 
```commandline
python -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
unless you want to do dev stuff and then you can replace the last line with:
```commandline
pip install -r requirements-dev.txt
```

## Running the game
You can run the game with:
```commandline
PORT=<PORT> python app.py
```
Configurations can be set in `config.py` (not part of the repo as it contains secrets).
If you want to use local SQLite (`word2vec.db`) set env var: `LITE=1`.


## Scripts
There are some useful scripts in the `scritps/` folder:

- `populate.py`: Given a Word2Vec model, will populate SQL table used by the game.
- `set_secret.py`: Well...
- `semantle.py`: A CLI version of the game. 

## Tests
Only for some of the logic right now, because I was lazy. Sorry.

## FAQ
The db (`word2vec.db`) is part of the repository due to ease of deployment to heroku.

If you find a free/cheap SQL server that can hold ~250MB I'll appreiciate it and will
remove it from the repo.

