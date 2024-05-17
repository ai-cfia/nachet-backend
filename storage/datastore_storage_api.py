"""
This module provide an absraction to the nachet-datastore interface.
"""
import datastore
from datastore import db, user
import datastore.bin.deployment_mass_import

import datastore.bin.upload_picture_set
import datastore.db.queries.seed as seed_queries
# import datastore.db.queries.user as user_queries
# import datastore.db.queries.picture as picture_queries


class DatastoreError(Exception):
    pass


class SeedNotFoundError(DatastoreError):
    pass


def get_cursor():
    db.connect_db()
    return db.cursor()


def get_all_seeds_names() -> list:

    """
    Return all seeds name register in the Datastore.
    """
    try:
        return seed_queries.get_all_seeds_names(get_cursor())
    except Exception as error: # TODO modify Exception for more specific exception
        raise SeedNotFoundError(error.args[0])


def get_seeds(expression: str) -> list:
    """
    Return a list of all seed that contains the expression
    """
    return list(filter(lambda x: expression in x, get_all_seeds_names(get_cursor())))


def validate_user(email: str) -> datastore.User:
    """
    Return True if user is valid, False otherwise
    """

    cursor = get_cursor()
    if user.is_user_registered(cursor, email):
        return datastore.get_User(email, cursor)


def upload_picture_set(**kwargs):
    return datastore.bin.upload_picture_set.upload_picture_set(get_cursor(), **kwargs)