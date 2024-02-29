# Testing documentation

To start the automatic test, you can use the following command:

```bash
python -m unittest discover -s tests
```

You also have the option to run automatic test in run_test.py or
manually test the functionality with the frontend. [See frontend testing
documentation](https://github.com/ai-cfia/nachet-frontend/blob/main/TESTING.md)

To perform the following test, you will need the frontend repository for the
Nachet Interactive's application. The frontend can be found at: [Nachet Frontend
GitHub Repository](https://github.com/ai-cfia/nachet-frontend).

You will also need the list of the available pipelines. The list can be found
[here](https://github.com/ai-cfia/nachet-backend/blob/51-implementing-2-models/docs/nachet-inference-documentation.md#available-version-of-the-json-file).

---

## Test Case: Populate model selection with pipelines information

**Objective**: Verify that the model selection component gets populated with the
pipeline information.

**Preconditions:**

- [ ] Nachet backend is set up and running. Use the command `hypercorn -b :8080
  app:app` to start the quartz server.
- [ ] The environment variables are all set.
- [ ] :exclamation: The frontend is not running yet

**Test Steps:**

1. Start the frontend application
1. Click on the model selection button
1. Validate that the current pipeline are selectable.

**Expected Results:**

- [ ] If a problem occur while retrieving the data, a error should have stop the
  server to start.
- [ ] If a problem occur while retrieving the data, but no error was raised, the
  model selection component will be empty.
- [ ] If everything went correctly while retrieving the data, the model
  selection component will display the pipeline metadata.

**Actual Results:**

- [ ] Describe the actual outcome of the test

**Pass/Fail Criteria:**

- [ ] Pass if the metadata from the available pipeline is display.
- [ ] Fail if the metadata from the available pipeline is not display and no
  error was raised.

---

## Test Case: Inference Request

**Objective**: Verify that the inference request endpoint `/inf` function as
expected.

**Preconditions:**

- [ ] Nachet backend is sep up and running. Use the command `hypercorn -b :8080
  app:app` to start the quartz server.
- [ ] The environment variable are all set.
- [ ] The frontend is running.
- [ ] Start the frontend application
- [ ] Click on the model selection button
- [ ] Validate that the current pipeline are selectable

**Test Steps:**

1. Upload a seed image
1. Select the first model (pipeline)
1. Click on the classify button
1. Wait until the result populate the canvas
1. Repeat the process for every model (pipeline)

|:boom: Warning|
|:--:|
|Displaying results from two different models will overlap and become unreadable.|

**Expected Results:**

- [ ] The data populate both the canvas and the results components with the
  prediction data from the model (pipeline).
- [ ] An alert with an error from port 3000 or 8080 is displayed.

**Actual Results:**

- [ ] Describe the actual outcome of the test

**Pass/Fail Criteria:**

- [ ] Pass if the data populate both the canvas and the results components with
  the prediction of the model (pipeline).
- [ ] Fail if an alert is launch with an error message.
- [ ] Fail if the data do not populate the canvas and the results components
- [ ] Fail if the inference is stuck in an infinite loops
