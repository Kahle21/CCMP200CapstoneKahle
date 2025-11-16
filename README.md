# CCMP200CapstoneKahle

# Serverless Image Processing Pipeline (CCMP200 Capstone)

This project implements a **serverless image processing pipeline** on AWS.  
When a user calls an API Gateway endpoint with the S3 object details, a Step Functions
state machine runs a Lambda function that resizes the image and stores a thumbnail
in a separate S3 bucket.

---

## Objective

- Practice using **S3, Lambda, Step Functions, API Gateway, and CloudWatch** together.
- Build a real, working **image resizing pipeline** using a serverless architecture.

---

## High-Level Architecture

```text
Client (HTTP POST)
       |
       v
+--------------+       +---------------------+       +--------------------+        +-------------------------+
| API Gateway  |  ---> | Step Functions      | --->  | Lambda (Pillow)    |  --->  | S3 (Resized Thumbnails) |
+--------------+       +---------------------+       +--------------------+        +-------------------------+
                                 ^
                                 |
                            CloudWatch Logs

2. AWS Resources & Identifiers (Concrete Values Used)

These are the actual resources used in this deployment:

Region: ca-central-1

S3 Buckets

Originals: ccmp200-original-images-kahle

Thumbnails: ccmp200-resized-images-kahle

Lambda

Function name: resize-image-lambda

Runtime: Python 3.11

Environment variable:

DEST_BUCKET = ccmp200-resized-images-kahle

Lambda Layer

Contains the Pillow library.

Provided via a public Lambda layer (e.g., Klayers) compatible with Python 3.11 in ca-central-1.

Step Functions

State machine name: ImageProcessingStateMachine

State machine ARN:
arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine

API Gateway (REST API)

API name: ImageProcessingAPI

Resource: /process-image

Method: POST

Deployed stage: prod

Final invoke URL:
https://1etwk7h22i.execute-api.ca-central-1.amazonaws.com/prod/process-image

IAM Roles

Lambda execution role (S3 + CloudWatch permissions).

Step Functions execution role (can invoke Lambda).

API Gateway execution role (can call states:StartExecution on the state machine).

3. Prerequisites

To deploy or reproduce this project, you need:

AWS Account

With access to: S3, Lambda, Step Functions, API Gateway, IAM, CloudWatch.

Region

This project uses ca-central-1 (Canada Central).

All resources should be created in the same region.

Image Processing Library (Layer)

A Lambda layer containing Pillow (Python image library).

The Lambda function is configured to use this layer.

If you were using Node.js instead of Python, an equivalent would be the sharp library.

Basic Tools (optional, but helpful)

git (to clone/push the repo).

Postman or curl (to test the HTTP endpoint).

4. Lambda Function Behavior

File: lambda_function.py

Runtime: Python 3.11

Dependencies: Pillow (provided via Lambda layer)

Expected event format:

{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}


Behavior:

Downloads key from bucket (original images).

Uses Pillow to:

Open the image.

Resize it to a thumbnail (using thumbnail((width, height))).

Saves the thumbnail to memory and uploads it to dest_bucket.

Writes it with a new key:
<original_name>_thumbnail.<ext>
e.g., elepahnt_thumbnail.jpg

Returns a JSON result to Step Functions:

{
  "status": "SUCCESS",
  "source_bucket": "...",
  "source_key": "...",
  "dest_bucket": "...",
  "dest_key": "...",
  "width": 200,
  "height": 200
}


If anything fails, it returns:

{
  "status": "FAILED",
  "errorMessage": "...",
  "bucket": "...",
  "key": "..."
}

5. Step Functions Workflow

File: state_machine_definition.json (exported from the console)

States:

ResizeImage (Task)

Invokes resize-image-lambda with input fields:

bucket, key, dest_bucket, width, height

Stores result at $.resizeResult

WasResizeSuccessful (Choice)

If $.resizeResult.status == "SUCCESS" → SuccessState

Else → FailState

SuccessState (Succeed)

FailState (Fail)

This provides clear pass/fail outcomes for the workflow.

6. API Gateway Integration

Method: POST /process-image

Integration type: AWS Service

Service: Step Functions

Action: StartExecution

Execution Role: IAM role that allows states:StartExecution on the state machine ARN.

Mapping template (application/json):

{
  "input": "$util.escapeJavaScript($input.body)",
  "name": "$context.requestId",
  "stateMachineArn": "arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine"
}


This passes the raw client JSON as the Step Functions input and uses an execution name based on the request ID.

7. Detailed Deployment Instructions

These steps assume a fresh deployment in ca-central-1.

Step 1 – Create S3 Buckets

Go to S3 → Create bucket.

Bucket 1 (originals):

Name: ccmp200-original-images-kahle

Bucket 2 (thumbnails):

Name: ccmp200-resized-images-kahle

Upload at least one test image to the originals bucket, e.g. elepahnt.jpg.

Step 2 – Create the Lambda Function

Go to Lambda → Create function.

Name: resize-image-lambda.

Runtime: Python 3.11.

Use or create an execution role that allows:

s3:GetObject on the originals bucket.

s3:PutObject on the thumbnails bucket.

CloudWatch Logs.

In Configuration → Environment variables:

DEST_BUCKET = ccmp200-resized-images-kahle

In the Code tab, paste the contents of lambda_function.py.

Attach the Pillow Lambda layer:

Configuration → Layers → Add a layer → select your Pillow layer (compatible with Python 3.11).

Test directly in Lambda using:

{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}


Confirm that elepahnt_thumbnail.jpg appears in the resized bucket.

Step 3 – Create the Step Functions State Machine

Go to Step Functions → Create state machine.

Choose Author with code.

Paste the JSON from state_machine_definition.json, ensuring:

Resource for the ResizeImage task is the Lambda ARN:
arn:aws:lambda:ca-central-1:695085239748:function:resize-image-lambda

The state machine name is ImageProcessingStateMachine.

Let AWS create an execution role for Step Functions.

Save and test with:

{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}


Confirm the execution ends in SuccessState.

Step 4 – Create API Gateway REST API

Go to API Gateway → Create API → REST API (Build).

API name: ImageProcessingAPI.

Create a resource /process-image.

Add a POST method:

Integration type: AWS Service

AWS Service: Step Functions

HTTP method: POST

Action: StartExecution

Execution role: an IAM role that allows states:StartExecution on
arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine.

In Integration Request → Mapping Templates:

Content-Type: application/json

Use the mapping template shown in Section 6.

Step 5 – Deploy API & Test

In API Gateway, click Actions → Deploy API.

Create/choose stage: prod.

Note the final URL:

https://1etwk7h22i.execute-api.ca-central-1.amazonaws.com/prod/process-image


Test (Postman, curl, or API Gateway Test):

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "bucket": "ccmp200-original-images-kahle",
    "key": "elepahnt.jpg",
    "dest_bucket": "ccmp200-resized-images-kahle",
    "width": 200,
    "height": 200
  }' \
  https://1etwk7h22i.execute-api.ca-central-1.amazonaws.com/prod/process-image


Verify:

API returns an executionArn and startDate.

Step Functions shows a successful execution.

S3 thumbnails bucket contains elepahnt_thumbnail.jpg.

8. Testing & Validation

Unit-level test (Lambda):
Use the Lambda console with a test event to ensure resizing works.

Workflow test (Step Functions):
Start an execution from the console and confirm all states are green.

End-to-end test (API):
Call the API Gateway URL and verify:

HTTP 200 response with executionArn.

Successful execution in Step Functions.

Thumbnail present in the resized S3 bucket.
