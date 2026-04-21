import re
from pathlib import Path
#import pathlib
from .datatypes import CleanedData

import csv
from typing import NamedTuple

DIR = Path(__file__).parent  / "data"

class CleanedData(NamedTuple):
    id: str
    org_name: str
    city: str
    zip: str

def zip_clean(zip_field, dict):
    zip_code = dict.get(zip_field).strip()
    zip_code = zip_code.split('-')[0]
    zip_code = (5-len(zip_code))*'0' + zip_code
  
    return zip_code 

PUNCTUATION = ".,?-#/()[]" 

def clean_address(address):
    address = address.lower()
    text_data = text_data.split(" ")
    cleaned_list = [word.strip(PUNCTUATION) for word in text_data]
    cleaned_list = [word for word in cleaned_list if word != ""]
    cleaned_list = [word for word in cleaned_list if word not in STOPWORDS]

def clean_ppp_data() -> list[CleanedData]:
    """
    This function should load the data from data/il-ppp.csv
    and return a list of CleanedData tuples.

    * For PPP data you should use the ID, BorrowerName, BorrowerCity, and BorrowerZip
    * All data should be converted to lowercase & stripped of leading and trailing whitespace.
    * All zip codes should be 5 digits long.

    Returns:
        A list of CleanedData items.
    """
    output_list = []
    file = DIR  / 'il-ppp.csv'
    with open(file, mode ='r') as file:
        csvFile = csv.DictReader(file)
        for line in csvFile:
            zip_code = zip_clean('BorrowerZip', line)
            tuple_for_export = CleanedData(line.get('ID'), line.get('BorrowerName').lower().strip(), line.get('BorrowerCity').lower().strip(), zip_code)
            output_list.append(tuple_for_export)
    return output_list 


def clean_opensecrets_data() -> list[CleanedData]:
    """
    This function should load the data from data/il_opensecrets.csv
    and return a list of CleanedData tuples.

    * Drop any rows where the Orgname is "Self Employed" with or without a hyphen.
    * All data should be converted to lowercase & stripped of leading and trailing whitespace.
    * All zip codes should be 5 digits long.

    Returns:
        A list of CleanedData items.
    """
    output_list = []
    file = DIR  / 'il_opensecrets_orgs.csv'
    with open(file, mode ='r') as file:
         csvFile = csv.DictReader(file)
         for line in csvFile:
             orgname = line.get('Orgname').lower()
             pattern = r'self[ -]employed'
             zip_code = zip_clean('Zip', line)

             if  not re.match(pattern, orgname):
                tuple_for_export = CleanedData(line.get('ID'), orgname.strip(), line.get('City').lower().strip(), zip_code)
                output_list.append(tuple_for_export)
    return output_list
