from typing import NamedTuple

# these constants should be used to indicate the match status of a pair
MATCH = "match"
NON_MATCH = "non-match"
MAYBE_MATCH = "maybe"

# these constants should be used to indicate the similarity of a pair
SIMILARITY_HIGH = "high"
SIMILARITY_MEDIUM = "medium"
SIMILARITY_LOW = "low"


class SimilarityTuple(NamedTuple):
    name_sim: str
    city_sim: str
    zip_match: bool


class CleanedData(NamedTuple):
    id: str
    org_name: str
    city: str
    zip: str
