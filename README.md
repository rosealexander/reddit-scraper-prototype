# Reddit Scraper prototype

Records the frequency of keyword mentions in comments on [r/all](https://www.reddit.com/r/all/).  
Data is recorded to a [PostgreSQL](https://www.postgresql.org) database via [Heroku](https://heroku.com).

## Installation

Use [npm](https://www.npmjs.com) to install.

```bash
npm install
```

## Usage

* Create a new Heroku application.
* Fork this repo and deploy it to the new Heroku app.
* Install the Heroku PostgreSQL Add-on.
* To start, run the free dyno web worker.

## Tools

* [PRAW](https://praw.readthedocs.io/en/latest/) Reddit API.  
* [psycopg](https://www.psycopg.org) PostgreSQL database adapter.  
* [Pip](https://pip.pypa.io/en/stable/) Python package installer.  
* [Heroku](https://heroku.com) Cloud Services.  

## License
[MIT](https://choosealicense.com/licenses/mit/)
