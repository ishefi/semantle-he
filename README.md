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
Configurations should be set in a `semantle.cfg` file, following the example `semantle.cfg.format`.
you should be using a mongo server for storing the vectors. Word2Vec model was trained as described (here)[https://github.com/Iddoyadlin/hebrew-w2v]


## Scripts
There are some useful scripts in the `scripts/` folder:

- `populate.py`: Given a Word2Vec model, will populate mongo collection used by the game.
- `set_secret.py`: Well...
- `semantle.py`: A CLI version of the game. 

## Tests
Only for some of the logic right now, because I was lazy. Sorry.

