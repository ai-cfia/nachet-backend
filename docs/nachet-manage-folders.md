# Manage folders

## Executive summary

A user is able to have a preview of his blob storage container in the Nachet
application. He can have many folders in his container and pictures in it. Since
we have the database, those folders are related to the picture_set table and
each pictures is also saved in the database. Here is the schema of actual
database.

``` mermaid
---
title: Extract from Nachet DB Structure 
---
erDiagram
  picture_set{
    uuid id PK
    json picture_set
    uuid owner_id FK
    timestamp upload_date
  }
  picture{
    uuid id PK
    json picture
    uuid picture_set_id FK
    uuid parent FK
    int nb_object
    boolean verified
    timestamp upload_date 
  }
inference{
    uuid id PK
    json inference 
    uuid picture_id FK
    uuid user_id FK
    timestamp upload_date
  }
  picture_seed{
    uuid id PK
    uuid picture_id FK
    uuid seed_id FK
    timestamp upload_date
  }
  picture_set ||--o{picture: contains
  picture ||--o{picture: cropped
  picture |o--o{picture_seed: has
  picture_seed }o--o| seed: has
  inference ||--o{ object: detects
  object ||--o{ seed_object: is
  seed_object }o--|| seed: is
  inference ||--|| picture: infers

```

From the nachet application, a user can create and delete folders, so the blob
storage and the database must be correctly updated.

When a folder is created, it takes on a name and is created as a picture_set in
the database and as a folder in the blob storage container of the user.

There are more issues when the user wants to delete a folder. If the folder
contains validated pictures, it may be useful for training purpose, because it
means there is a valid inference associate with each seed on the picture. The
same applies to pictures imported in batches, which have been downloaded for
training purposes. Our solution is to request confirmation from the user, who
can decide to delete pictures from his container but let us save them, or he can
delete everything anyway, for example if there has been a missed click.

## Prerequisites

- The user must be signed in and have an Azure Storage Container
- The backend need to have a connection with the datastore

## Sequence Diagram

### Delete use case

```mermaid
sequenceDiagram
    participant User
    participant FE
    participant BE
    participant DS

    User->>FE: Delete Folder
    rect rgb(200, 50, 50)
      FE->>BE: /delete-request
    end
    rect rgb(200, 50, 50)
          BE->>DS: Check if there are validated inferences or pictures from a batch import
note left of DS: Check for picture_seed entities linked to picture id<br> since a verified inference and a batch upload has those
    end
    alt picture_seed exist
        DS-->>BE: Validated inference status or pictures from batch import
        BE->>FE: True : Request user confirmation
        rect rgb(200, 50, 50)
            FE->>User: Ask to keep data for training
note left of FE : "Some of those pictures were validated or upload via the batch import.<br>Do you want us to keep them for training ? <br>If yes, your folder will be deleted but we'll keep the validated pictures.<br>If no, everything will be deleted and unrecoverable.
        end
        alt No
            User ->>FE: delete all
            rect rgb(200, 50, 50)
                FE-->BE:  /delete-permanently
            end
            BE->>DS: delete picture_set
        else YES
            User ->>FE: Keep them
            rect rgb(200, 50, 50)
                FE-->BE: /delete-with-archive
            end
            rect rgb(200, 50, 50)
                BE->>DS: archive data for validated inferences and batch import in picture_set
                    note left of DS: "Pictures are moved in different container <br> DB entities updated" 
                BE->>DS: delete picture_set
                   note left of DS: "Folder and all the files left are deleted, <br>related pictures, inference are deleted." 
            end
       else CANCEL
            User ->>FE: cancel : nothing happens
       end
    else no picture_seed exist
        DS-->>BE: No pictures with validated inference status or from batch import
        BE-->>FE: False: confirmation to delete the folder
        rect rgb(200, 50, 50)
            FE->>User: Ask confirmation
note left of FE : "Are you sure ? Everything in this folder will be deleted and unrecoverable"
        end
        alt Yes
            User ->>FE: delete all
            rect rgb(200, 50, 50)
                FE-->BE:  /delete-permanently
            end
            BE->>DS: delete picture_set
        else CANCEL
            User ->>FE: cancel : nothing happens
        
        end
    end

```

## API Routes

### /create-dir

The `create-dir` route need a folder_name and create the folder in database and
in Azure Blob storage.

### /get-directories

The `get-directories` route retreives all user directories from the database
with their pictures as a json. There is 4 different cases for the pictures :

| **is_verified \\ inference_exist** | **false**              | **true**             |
|------------------------------------|----------------------|-----------------------|
| **false**                           | *should not happend* | inference not verified  |
| **true**                          | batch import | inference verified |

```json
{
"folders" : [
        {
            "picture_set_id" : "xxxx-xxxx-xxxx-xxxx",
            "folder_name" : "folder name",
            "nb_pictures": 4,
            "pictures" : [
                {
                    "picture_id" : "xxxx-xxxx-xxxx-xxxx",
                    "inference_exist": false,
                    "is_validated": true
                },
                ...
            ]
        },
        ...
    ]
}
```

### /get-picture

The `get-picture` route retreives selected picture as a json :

```json
{
    "picture_id" : "xxxx-xxxx-xxxx-xxxx",
    "inference": {
     }
    "image": "data:image/...;base64,xxxxxxxx"
}
```

### /delete-request

The `delete-request` route return True if there is validated pictures in the
given folder or False else.

### /delete-permanently

THe `delete-permanently`route delete the given folder, it means it delete the
picture_set and every things related in database, and it delete all blobs in the
azure blob storage.

### /delete-with-archive

The `delete-with-archive` route delete the given folder from the user container
but move everything in it n the dev container.
