# Assistance Program Watcher 
### Home assignment by TailorMed
In this exercise I create a monitoring tool that, using scraping on the website, updates our local system (using remote DB) about the open/closed status of the assistance programs and displays them in our website.

In any case of missing information about the status, the default value will be closed.


## Run the app

first clone the project from GitHub, into a known location

Open two terminals within the project location.

First terminal - Inside the project directory perform these commands:
```bash
1. virtualenv env
2. env\scripts\activate
3. pip install -r requirements.txt
4. python manage.py runserver                             if needed: (username: inbar, password: inbar12345)
```

Second terminal - Inside the project directory perform these commands:
```bash
1. virtualenv env
2. env\scripts\activate
3. pip install -r requirements.txt
4. celery -A backend worker -l info
```

## Usage
Click the local host url, it will appear in the first terminal like this:
```bash
Starting development server at http://127.0.0.1:8000/
```
Now you can see the data which have been collected by the web scraper and which have been inserted into our remote MySQL DB.

By refreshing the page, the data will be updated.

In order to stop running - close both terminals.


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## What's next?
UI implementation. 

Refreshing data on a click.

Upload app to remote host.

Implement other API requests, e.g. get program data by name.
