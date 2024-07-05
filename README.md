# Papernest project

## Description

Provide an API to real estate agencies that will allow them to get the network coverage for all the homes they are
renting.

### Requirements

* python (>3.10)
*  pip

### Set environnment

* Create a python env &rarr; python -m venv <name_of_virtual_env>
* Install the requirements &rarr; pip install requirements.txt

### Run server

* To run the server &rarr; uvicorn main:app --reload

### Query

* To test the API
    1. Go to Postman
    2. Send a POST request on '/coverage'
    3. The body of the request is this form:     
       {
       "addresses": {"id1": "157 boulevard Mac Donald 75019 Paris",
                     "id2": "6 rue Montgallet 75012 Paris"}
       }
   4. You'll get the network coverage results for each address
   
### Test

* To launch the tests &rarr; pytest tests/test_utils.py
 


