# BasketRadar Data Processing

## Prequisites

* Python 3 (recent 3.11 or 3.12 preferred)

## (Optional) Create a Virtual Environment

1. Create a virtual environment to which packages can be installed. From within the `webapp` folder, run:  
  `python -m venv .venv`

2. Activate your virtual environment:  
  `.venv\Scripts\Activate.ps1` from Powershell or `source .venv/Scripts/activate` from bash or `source .venv/bin/activate` for Mac.

## Installing Dependencies

* To install saved dependencies:  
  `pip install -r requirements.txt`

* To save new dependencies:  
  1. `pip install <dependency>`
  2. `pip freeze > requirements.txt`

## Running the Web App

* Call data processing script from the command line:  
  `python load_and_clean_data.py`