"""
This module provide an absraction to the nachet-datastore interface.
"""
import datastore
from datastore import db
from datastore import user as user_datastore
import datastore.bin.deployment_mass_import

import datastore.bin.upload_picture_set
import datastore.db.queries.seed as seed_queries

class DatastoreError(Exception):
    pass

class SeedNotFoundError(DatastoreError):
    pass

class GetPipelinesError(DatastoreError):
    pass

class UserNotFoundError(DatastoreError):
    pass

def get_connection() :
    return db.connect_db()

def get_cursor(connection):
    return db.cursor(connection)
 
def end_query(connection, cursor):
    db.end_query(connection, cursor)
 
def get_all_seeds() -> list:

    """
    Return all seeds name register in the Datastore.
    """
    try:
        connection = get_connection()
        cursor = get_cursor(connection)
        return datastore.get_seed_info(cursor)
    except Exception as error: # TODO modify Exception for more specific exception
        raise SeedNotFoundError(error.args[0])


def get_all_seeds_names() -> list:

    """
    Return all seeds name register in the Datastore.
    """
    try:
        connection = get_connection()
        cursor = get_cursor(connection)
        return seed_queries.get_all_seeds_names(cursor)
    except Exception as error: # TODO modify Exception for more specific exception
        raise SeedNotFoundError(error.args[0])

def get_seeds(expression: str) -> list:
    """
    Return a list of all seed that contains the expression
    """
    connection = get_connection()
    cursor = get_cursor(connection)
    return list(filter(lambda x: expression in x, get_all_seeds_names(cursor)))

def get_user_id(email: str) -> str:
    """
    Return the user_id of the user
    """
    connection = get_connection()
    cursor = get_cursor(connection)
    if user_datastore.is_user_registered(cursor, email):
        return user_datastore.get_user_id(cursor, email)
    else :
        raise UserNotFoundError("User not found")
                                      
async def create_user(email: str, connection_string) -> datastore.User:
    """
    Return True if user is valid, False otherwise
    """
    connection = get_connection()
    cursor = get_cursor(connection)
    user = await datastore.new_user(cursor, email, connection_string)
    end_query(connection, cursor)
    return user


async def get_picture_id(cursor, user_id, image_hash_value, container_client) :
    """
    Return the picture_id of the image
    """
    picture_id = await datastore.upload_picture_unknown(cursor, str(user_id), image_hash_value, container_client)
    return picture_id

def upload_pictures(cursor, user_id, picture_set_id, container_client, pictures, seed_name: str, zoom_level: float = None, nb_seeds: int = None) :
    try :
        return datastore.upload_pictures(cursor, user_id, picture_set_id, container_client, pictures, seed_name, zoom_level, nb_seeds)
    except Exception as error:
        raise DatastoreError(error)
    
async def create_picture_set(cursor, container_client, user_id: str, nb_pictures: int, folder_name = None):
    try :
        return await datastore.create_picture_set(cursor, container_client, nb_pictures, user_id, folder_name)
    except Exception as error:
        raise DatastoreError(error)

async def get_pipelines() -> list:

    """
    Retrieves the pipelines from the Datastore
    """
    try:
        connection = get_connection()
        cursor = get_cursor(connection)
        pipelines = await datastore.get_ml_structure(cursor)
        return pipelines
    except Exception as error: # TODO modify Exception for more specific exception
        raise GetPipelinesError(error.args[0])

async def save_inference_result(cursor, user_id:str, inference_dict, picture_id:str, pipeline_id:str, type:int):
    return await datastore.register_inference_result(cursor, user_id, inference_dict, picture_id, pipeline_id, type)

async def save_perfect_feedback(cursor, inference_id:str, user_id:str, boxes_id):
    await datastore.new_perfect_inference_feeback(cursor, inference_id, user_id, boxes_id)
    
async def save_annoted_feedback(cursor, feedback_dict):
    await datastore.new_correction_inference_feedback(cursor, feedback_dict)

async def delete_directory(cursor, picture_set_id):
    await datastore.delete_picture_set(cursor, picture_set_id)
    
async def get_directories(cursor, user_id):
    try :
        return await datastore.get_picture_sets_info(cursor, user_id)
    except Exception as error:
        raise DatastoreError(error)