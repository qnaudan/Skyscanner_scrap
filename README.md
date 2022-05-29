# Web Scraping personal project

Gathering airflight fares on Skyscanner website.

Back in 2018, I needed to monitor airflight fares during a stay abroad. I spent a few afternoons in a Starbucks coffee to learn what was required.

This project involves browser automation with [Selenium](https://selenium-python.readthedocs.io/) and [multiprocessing](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing) to deal with several browsers.

Here's a user-friendly app.

## Installation

Create the directory below to store files of saved data

```bash
mkdir workbooks
```

Install or update required libraries

```bash
pip install -r requirements.txt
```

Launch the app

```bash
python3 main.py -d Paris -a Bangkok -s 20220801 --days 40
```

## Usage

They are 5 keys parameters the user can modify :

- Departure and Destination cities are inputs (no particular syntax, the search engine find as if you key manually)

- An expected number of days of stay in the destination is key in, the app will also look shorter and longer stay opportunities up to 50% of this number (write down 0 day for One-Way flights)

- 2 additional variables are in the code and not asked on prompting : the starting day to look up the first flight (like 30 days from now) and the span of search in days (the 60 next days for instance). User is invited to write manually inside the code what he prefers best.


## Bot detection

On the first opening of the browser window (where Desparture and Destination cities are wrote down in search engine to get the correct URL syntax), a captcha test may appear, then it is the only time the user is asked to initialise and pass the captcha test within 100 seconds.
