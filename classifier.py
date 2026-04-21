from pathlib import Path

from collections import defaultdict
import itertools
from .datatypes import MATCH, NON_MATCH, MAYBE_MATCH, SimilarityTuple
from .clean import clean_opensecrets_data, clean_ppp_data
from .similarity import calculate_similarity_tuple
import csv



DIR = Path(__file__).parent  / "data"



def sort_similarities(sim_list):
    """
    This function takes a list of tuples containing SimilarityTuples and their
    corresponding likelihoods and sorts the list from highest to lowest likelihood
    of representing a match.

    Inputs:
        `sim_list` should be a list of tuples where each tuple contains a
        SimilarityTuple and two floats representing the likelihood of the tuple
        representing a match and the likelihood of the tuple representing a
        non-match.

    Returns:
        Sorted list of tuples in the same format as the input list.

    Example:

    [
        (SimilarityTuple("high", "high", True), 0.8, 0.1),
        (SimilarityTuple("high", "medium", True), 0.9, 0.2),
        ... # more rows
    ]

    """
    if len(sim_list) != 18:
        raise ValueError("sim_list must have 18 elements")
    if len(sim_list[0]) != 3:
        raise ValueError("sim_list must have 3 elements per tuple")

    def sort_key(sim_tuple):
        if sim_tuple[2] == 0:
            return sim_tuple[1] * 100000000  # boost to front
        return sim_tuple[1] / sim_tuple[2]

    return sorted(sim_list, key=sort_key, reverse=True)

def import_data(filename): 
    """
    Imports either the matches.csv or non_matches.csv 
    Returns:
        A list of tuples for each os_id-ppp_id pair
    """

    output_list = []
    file = DIR  / filename
    with open(file, mode ='r') as file:
        csvFile = csv.DictReader(file)
        for line in csvFile:
            os_id = line.get("os_id")
            ppp_id = line.get("ppp_id")
            
            output_list.append((os_id, ppp_id))
    return output_list 

def baseline_create():
    """
    Creates a baseline dictionary with all 18 similarity tuples for the matches and non-matches datasets 
    """
    dict_name = {}
    for part1 in ["low", "medium", "high"]:
        for part2 in ["low", "medium", "high"]:
            for part3 in [True, False]:
                similartuple = SimilarityTuple(part1, part2, part3)
                dict_name[similartuple] = 0 
    return dict_name

def dictionary_update(sample_data, opensecrets_data, ppp_data, input_dict):
    """
    Determines the counts of each similarity tuple in the sample_data 

    Inputs:
        sample_data: Either the matches.csv or non_matches.csv
        opensecrets_data: The cleaned data from data/il_opensecrets.csv
        ppp_data: The cleaned data from data/il-ppp.csv

    Returns:
        An intermediate dictionary updating the input_dict with the number of times each similarity tuple is in the sample_data 
    """ 
    for tuple_combo in sample_data: 
        tup_opensec = opensecrets_data.get(tuple_combo[0])
        tup_ppp = ppp_data.get(tuple_combo[1])
        similar_score = calculate_similarity_tuple(tup_opensec, tup_ppp)
        input_dict[similar_score] = input_dict.get(similar_score) + 1
    return input_dict

def calculate_matches(list_tuples, max_false_positives, final_dictionary):
    """
    Determines which similarity tuples should be classified as matches and produces an intermediate dictionary 
    representing the final dictionary state with those matches applied

    Inputs:
        list_tuples (list): List of similarity tuples and their match/non-match probabilities 
        max_false_positives (float): The maximum rate of false positives
            the classifier is allowed to have.
        final_dictionary (dict): Final dictionary with matching status for each similarity tuple


    Returns:
        An intermediate dictionary representing final dictionary state with those matches applied
    """  
    ### Step 1: Create an independent list for the match tuples
    match_list = [] 
    total_error = 0 
    ### Step 2: Identify which tuples should be inserted into match_list based on the max_false_positives threshold 
    for tuple_obj in list_tuples:
        if total_error + tuple_obj[2] > max_false_positives:
            break
        total_error = total_error + tuple_obj[2]
        match_list.append(tuple_obj)

    ### Step 3: In the final dictionary, assign MATCH to the similarity tuple keys in the match_list
    for tuple_obj in match_list:
        final_dictionary[tuple_obj[0]] = MATCH
        list_tuples.remove(tuple_obj)
        
    return final_dictionary

def calculate_nonmatches(list_tuples, max_false_negatives, final_dictionary):
    """
    Determines which similarity tuples should be classified as non-matches and produces an intermediate dictionary 
    representing the final dictionary state with those non-matches applied

    Inputs:
        list_tuples (list): List of similarity tuples and their match/non-match probabilities 
        max_false_negatives (float): The maximum rate of false negatives
            the classifier is allowed to have.
        final_dictionary (dict): Final dictionary with matching status for each similarity tuple

    Returns:
        An intermediate dictionary representing final dictionary state with those non-matches applied
    """    
    ### Step 1: Create an independent list for the non-match tuples 
    non_match_list = [] 
    total_error = 0 
    ### Step 2: Identify which tuples should be inserted into non_match_list based on the max_false_negatives threshold 
    for tuple_obj in list_tuples:
        if total_error + tuple_obj[1] > max_false_negatives:
            break
        total_error = total_error + tuple_obj[1]
        non_match_list.append(tuple_obj)

    ### Step 3: In the final dictionary, assign NON_MATCH to the similarity tuple keys in the non_match_list
    for tuple_obj in non_match_list:
        final_dictionary[tuple_obj[0]] = NON_MATCH
        list_tuples.remove(tuple_obj)
    return final_dictionary

def final_dictionary(list_tuples, max_false_positives, max_false_negatives):
    """
    Output the dictionary mapping similarity tuples to match types using the
    final list of tuples and their probabilities  

    Inputs:
        list_tuples (list): List of similarity tuples and their match/non-match probabilities 
        max_false_positives (float): The maximum rate of false positives
            the classifier is allowed to have.
        max_false_negatives (float): The maximum rate of false negatives
            the classifier is allowed to have.

    Returns:
        A dictionary mapping similarity tuples to match types.
        There must be one entry for each possible similarity tuple.
    """
    ### Pull together the file dictionary and sort the tuples list  
    final_dictionary = {}
    list_tuples = sort_similarities(list_tuples)
    
    ##### Step 1: Immediately Pull out the Maybe tuples 
    maybe_list = [item for item in list_tuples if item[1] == 0 and item[2] == 0]

    for tuple_obj in maybe_list:
        final_dictionary[tuple_obj[0]] = MAYBE_MATCH
        list_tuples.remove(tuple_obj)
    
    ##### Step 2: Pull out and calculate the Match tuples  
    final_dictionary = calculate_matches(list_tuples, max_false_positives, final_dictionary)

    if not list_tuples:
        return  final_dictionary

    ##### Step 3: Pull out and calculate the non-Match tuples      
    list_tuples.reverse()
    final_dictionary = calculate_nonmatches(list_tuples, max_false_negatives, final_dictionary)

    if not list_tuples:
        return  final_dictionary
    
    ##### Step 4: Assign MAYBE MATCH to the remaining, unassigned tuples  
    for remaining in list_tuples:
        final_dictionary[remaining[0]] = MAYBE_MATCH
    
    return final_dictionary

                

def train_classifier(max_false_positives: float, max_false_negatives: float):
    """
    Train a classifier using the training data and the given
    maximum false positives and false negatives.

    Inputs:
        max_false_positives (float): The maximum rate of false positives
            the classifier is allowed to have.
        max_false_negatives (float): The maximum rate of false negatives
            the classifier is allowed to have.

    Returns:
        A dictionary mapping similarity tuples to match types.
        There must be one entry for each possible similarity tuple.
    """
    ### Step 1: Clean and import data 
    clean_tuple_opensec = clean_opensecrets_data()
    clean_tuple_ppp = clean_ppp_data()
    matches = import_data('matches.csv')
    non_matches = import_data('non_matches.csv')

    ### Step 2: Create dictionary for the cleaned datafiles for matching 
    opensecrets = {clean_tuple.id: clean_tuple for clean_tuple in clean_tuple_opensec}
    ppp = {clean_tuple.id: clean_tuple for clean_tuple in clean_tuple_ppp}
    total_matches = len(matches)
    total_nonmatches = len(non_matches)

    ### Step 3: Run helper fuctions to create baseline dictionaries with each similarity tuple 
    match_probabilities = baseline_create()
    non_match_probabilities = baseline_create()

    ### Step 4: Run helper fuctions to update baseline dictionaries with counts of each similarity tuple 
    match_probabilities = dictionary_update(matches, opensecrets, ppp, match_probabilities)
    non_match_probabilities = dictionary_update(non_matches, opensecrets, ppp, non_match_probabilities)

    ### Step 5: Create list of tuples of similarity tuples and their respective match/non-match probabilities 
    list_tuples = []
    for key in match_probabilities.keys():
        list_tuples.append((key, match_probabilities[key]/total_matches, non_match_probabilities[key]/total_nonmatches))
           
    ### Step 6: Run helper to pull together the final dictionary for output 
    return final_dictionary(list_tuples, max_false_positives, max_false_negatives)
    


def find_matches(
    max_false_positives,
    max_false_negatives,
    *,  # all arguments after this must be specified by keyword
    # (e.g. find_matches(0.1, 0.2, max_matches=10)
    max_matches=float("inf"),
    block_on_city=False,
):
    """
    Find matches between the PPP data and the OpenSecrets data.

    Inputs:
        max_false_positives (float): The maximum rate of false positives
            the classifier is allowed to have.
        max_false_negatives (float): The maximum rate of false negatives
            the classifier is allowed to have.
        max_matches (int): The maximum number of matches to return.
        block_on_city (bool): Whether or not to block on city when
            determining matches. Defaults to False.

    Returns:
        A list of tuples containing the OpenSecrets row, the PPP row,
        and the similarity classification of the match.

        Each tuple in the list is in the form:
            (cleaned_row_from_os, cleaned_row_from_ppp, similarity_tuple)
    """
    
    # Step 1) Train the classifier.
    classifier = train_classifier(max_false_positives, max_false_negatives)

    # Step 2) Load the PPP and OpenSecrets data.
    clean_tuple_opensec = clean_opensecrets_data()
    clean_tuple_ppp = clean_ppp_data()

    # Step 3) Create a list of matches using your classifier.
    #        If block_on_city is True, only consider matches where the city is the same.
    #        If the number of matches exceeds max_matches, stop searching.

    output_list = []
    for opensec in clean_tuple_opensec:
        for ppp in clean_tuple_ppp:
           
           if block_on_city == True and opensec.city != ppp.city:
               continue
           similar_score = calculate_similarity_tuple(opensec, ppp)
           if classifier[similar_score] == MATCH:
               output_list.append((opensec, ppp, similar_score))
               if len(output_list) >= max_matches:
                   return output_list
    return output_list
