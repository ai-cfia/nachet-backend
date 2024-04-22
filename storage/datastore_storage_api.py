
"""
This module provide an absraction to the nachet-datastore interface.
"""
import datastore
from datastore import db

class DatastoreError(Exception):
    pass

class SeedNotFoundError(DatastoreError):
    pass

def get_connection():
    return db.connect_db()

def get_cursor(connection):
    return db.cursor()

def get_all_seeds_names() -> list:

    """
    Return all seeds name register in the Datastore.
    """
    try:
        return db.queries.seed.get_all_seeds_names(get_cursor)
    except Exception as error: # TODO modify Exception for more specific exception
        raise SeedNotFoundError(error.args[0])

def get_seeds(expression: str) -> list:
    """
    Return a list of all seed that contains the expression
    """
    return list(filter(lambda x: expression in x, get_all_seeds_names(get_cursor)))