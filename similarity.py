from .datatypes import CleanedData, SimilarityTuple
from .datatypes import SIMILARITY_HIGH, SIMILARITY_LOW, SIMILARITY_MEDIUM
import jellyfish
from typing import NamedTuple
from pathlib import Path



DIR = Path(__file__).parent  / "data"

class SimilarityTuple(NamedTuple):
    name_sim: str
    city_sim: str
    zip_match: bool

def rate(score):
    if score >= 0.95:
        return "high"
    if score < 0.95 and score >= 0.80:
        return "medium"
    return "low"    

def calculate_similarity_tuple(
    tuple1: CleanedData, tuple2: CleanedData
) -> SimilarityTuple:
    """
    This function should take two tuples and return a similarity tuple
    describing the similarity of the two tuples.

    Inputs:
        tuple1: A CleanedData tuple
        tuple2: A CleanedData tuple

    Returns:
        A SimilarityTuple representing the similarity between the two
        data tuples.
    """

    name_sim = jellyfish.jaro_winkler_similarity(tuple1.org_name, tuple2.org_name)
    city_sim = jellyfish.jaro_winkler_similarity(tuple1.city, tuple2.city)
    zip_match = tuple1.zip == tuple2.zip

    return SimilarityTuple(rate(name_sim),rate(city_sim), zip_match)