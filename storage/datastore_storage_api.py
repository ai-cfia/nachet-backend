"""
This module provide an absraction to the nachet-datastore interface.
"""
from hmac import new
import datastore
from datastore import db
from datastore import user as user_datastore
import datastore.bin.deployment_mass_import

import datastore.bin.upload_picture_set
import datastore.db.queries.seed as seed_queries
import datastore.db.queries.machine_learning as ml_queries
# import datastore.db.queries.user as user_queries
# import datastore.db.queries.picture as picture_queries


class DatastoreError(Exception):
    pass


class SeedNotFoundError(DatastoreError):
    pass

class GetPipelinesError(DatastoreError):
    pass


def get_cursor():
     return db.cursor(db.connect_db())


def get_all_seeds() -> list:

    """
    Return all seeds name register in the Datastore.
    """
    try:
        return seed_queries.get_all_seeds(get_cursor())
    except Exception as error: # TODO modify Exception for more specific exception
        raise SeedNotFoundError(error.args[0])


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


async def validate_user(email: str, connection_string) -> datastore.User:
    """
    Return True if user is valid, False otherwise
    """

    cursor = get_cursor()
    if user_datastore.is_user_registered(cursor, email):
        user = datastore.get_User(email, cursor)
    else :
        user = await datastore.new_user(cursor, email, connection_string)
    return user


async def get_picture_id(user_id, image_hash_value, container_client) :
    """
    Return the picture_id of the image
    """
    cursor = get_cursor()
    print("sfbvfvzs")
    picture_id = await datastore.upload_picture(cursor, str(user_id), image_hash_value, container_client)
    print(picture_id)
    return picture_id

def upload_picture_set(**kwargs):
    return datastore.bin.upload_picture_set.upload_picture_set(get_cursor(), **kwargs)

async def get_pipelines() -> list:

    """
    Retrieves the pipelines from the Datastore
    """
    try:
        pipelines = await datastore.get_ml_structure(get_cursor())
        return pipelines
    except Exception as error: # TODO modify Exception for more specific exception
        raise GetPipelinesError(error.args[0])

async def save_inference_result(user_id:str, inference_dict, picture_id:str, pipeline_id:str, type:int):
    print(user_id)
    print(picture_id)
    return await datastore.register_inference_result(get_cursor(), user_id, inference_dict, picture_id, pipeline_id, type)

async def save_perfect_feedback(inference_id:str, user_id:str):
    # peut-être --> user_id = user.get_user_id(cursor, email) (genre j'ai l'email et pas le id direct)
    await datastore.register_perfect_inference_feeback(inference_id, user_id, get_cursor())
    
async def save_annoted_feedback(inference_id:str, user_id:str, inference_feedback:dict):
    # peut-être --> user_id = user.get_user_id(cursor, email) (genre j'ai l'email et pas le id direct)
    await datastore.register_annoted_inference_feeback(inference_id, user_id, inference_feedback, get_cursor())
    