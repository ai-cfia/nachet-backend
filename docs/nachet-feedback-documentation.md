# User inference feedback

## Executive summary

When seed analysts use Nachet, they should be able to give their retroaction on
the result. A pipeline of action needs to be integrated from the Frontend to the
database to be able to register the user feedback. The possible feedbacks types
are:

- A perfect feedback (Doesn't change anything and validate the inference)
- A new guess is given by the analyst
- The box coordinates have changed
- The box is deleted (not a seed)
- A new box is added

## Prerequisites

- The user must be signed in and have an Azure Storage Container
- The backend need to have a connection with the datastore
- The user can do an inference request

## Solution

The analyst selects the box for which he or she wishes to give feedback, and
then fills in a form containing a series of information about its correction.
The front end adapts this information and sends it to the back end, then,
according to each case of feedback, the datastore updates the inference and the
object.

## Sequence Diagram

``` mermaid

sequenceDiagram;
  actor User
  participant Frontend
  participant Backend
  participant Datastore
  participant Database
  

    User ->> Frontend: Validate inference
    alt Perfect Inference
    Frontend -) Backend: Inference result positive (user_id, boxes)
    Backend -) Datastore: new_perfect_inference_feeback(inference_id, user_id, boxes_id)
    Note over Backend, Datastore : Each box_id is an inference object in db
        alt if inference not already verified
            Datastore ->> Database: Set each object.valid = True & object.verified_id=object.top_id
        end
    else Annotated Inference
    Frontend -) Backend: Inference feedback (inference_feedback.json,user_id,inference_id)
    Backend ->> Datastore: Inference feedback (inference_feedback.json, user_id, inference_id)
    Datastore -> Database: Get Inference_result(inference_id)
        loop each Boxes
            alt box has an id value
                alt inference_feedback.box.verified= False
                    Datastore --> Datastore: Next box & flag_all_box_verified=False
                else
                    Datastore -) Database: Set object.verified=True & object.verified_by=user_id
                    Datastore -) Datastore: Compare label & box coordinate
                    alt label value empty
                        Datastore -) Database: Set object.top_inference=Null
                        Datastore -) Database: Set object.modified=False                   
                    else label or box coordinate are changed & not empty
                        Datastore -) Database: Update object.top_inference & object.box_metadata
                        Note over Datastore,Database: if the top label is not part of the seed_object guesses, <br>we will need to create a new instance of seed_object.
                        Datastore -) Database: Set object.modified=true
                    else label and box haven't changed
                        Datastore -) Database: Set object.modified=False
                    end
                end
            else box has no id value
                Datastore -) Database: Create new object and seed_object
            end
        end
    end
    Datastore -) Datastore : verify_inference_status(inference_id, user_id)
    Note over Datastore, Database : set inference verified if all objects have a verified_id

```

## API Routes

### /get-user-id

The `/get-user-id` route retrieve the user-id for a given email.

### /seeds

The `/seeds` is the route to call to get the all the seeds names needed for the
frontend to build the form to upload the pictures to the database.

### /feedback-positive

The `/feedback-positive` route is the endpoint that the frontend call to add a
positive feedback to an inference, giving the inference and the box to validate.

### /feedback-negative

The `/feedback-negative` route is the API endpoint that send the informations to
the datastore so a correction feedback is added to a given inference and box.
