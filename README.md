# CCMP200CapstoneKahle

## Serverless Image Processing Pipeline (CCMP200 Capstone)

This project implements a **serverless image processing pipeline** on AWS.  
When a user calls an API Gateway endpoint with S3 object details, a Step Functions
state machine runs a Lambda function that resizes the image and stores a thumbnail
in a separate S3 bucket.

---

## 1. Objective

- Use **S3, Lambda, Step Functions, API Gateway, and CloudWatch** together in one workflow.
- Build a real, working **image resizing pipeline** using a serverless architecture.
- Demonstrate logging, orchestration, and HTTP-based invocation of a serverless workflow.

---

## 2. High-Level Architecture

### 2.1 Diagram

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
2.2 Flow Summary
Client sends an HTTP POST request to the API Gateway /process-image endpoint.

API Gateway calls StartExecution on the Step Functions state machine.

Step Functions invokes the resize-image-lambda function.

Lambda:

Reads the original image from the originals S3 bucket.

Resizes it using Pillow.

Saves the thumbnail in the thumbnails S3 bucket.

Step Functions evaluates the Lambda result:

SUCCESS → Succeed state.

FAILED → Fail state.

CloudWatch Logs capture Lambda and Step Functions execution details.

3. AWS Resources & Identifiers (Concrete Values Used)
These are the actual resources used in this deployment.

3.1 Region
Region: ca-central-1 (Canada Central)

3.2 S3 Buckets
Original Images Bucket:
ccmp200-original-images-kahle

Resized Thumbnails Bucket:
ccmp200-resized-images-kahle

3.3 Lambda
Function name: resize-image-lambda

Runtime: Python 3.11

Environment variable:

DEST_BUCKET = ccmp200-resized-images-kahle

3.4 Lambda Layer (Pillow)
Contains the Pillow image processing library.

Provided via a public Lambda layer (e.g., Klayers) compatible with:

Runtime: Python 3.11

Region: ca-central-1

Attached to the resize-image-lambda function.

3.5 Step Functions
State machine name: ImageProcessingStateMachine

State machine ARN:

text
Copy code
arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine
3.6 API Gateway (REST API)
API name: ImageProcessingAPI

Resource: /process-image

Method: POST

Stage: prod

Final invoke URL:

text
Copy code
https://1etwk7h22i.execute-api.ca-central-1.amazonaws.com/prod/process-image
3.7 IAM Roles (Conceptual)
Lambda execution role:

Permissions:

s3:GetObject on ccmp200-original-images-kahle

s3:PutObject on ccmp200-resized-images-kahle

CloudWatch Logs (for Lambda)

Step Functions execution role:

Permissions:

lambda:InvokeFunction on resize-image-lambda

API Gateway execution role:

Permissions:

states:StartExecution on
arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine

4. Prerequisites
To deploy or reproduce this project, you need:

4.1 AWS Account & Services
Active AWS account with access to:

Amazon S3

AWS Lambda

AWS Step Functions

Amazon API Gateway

AWS IAM

Amazon CloudWatch

4.2 Region
All resources are deployed in:

ca-central-1 (Canada Central)

All services (S3, Lambda, Step Functions, API Gateway) should be in the same region.

4.3 Image Processing Library (Layer)
A Lambda layer containing the Pillow library:

Language: Python

Version: Python 3.11

The Lambda function is configured to use this layer.

(If using Node.js instead of Python, the equivalent would typically be the sharp library.)

4.4 Optional Tools
git – for cloning/pushing the repository.

Postman or curl – to test the HTTP endpoint.

5. Lambda Function Behavior
File: lambda_function.py
Runtime: Python 3.11
Dependency: Pillow (provided via Lambda layer)

5.1 Expected Event Format
json
Copy code
{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}
5.2 Behavior Summary
Input:

Reads bucket, key, dest_bucket, width, and height from the event.

Download original image:

Uses s3.get_object(Bucket=bucket, Key=key) to read the original image from S3.

Resize image with Pillow:

Opens the image using Pillow.

Resizes it to a thumbnail with:

img.thumbnail((width, height))

Generate thumbnail key:

New key format:
<original_name>_thumbnail.<ext>
Example: elepahnt_thumbnail.jpg

Upload thumbnail:

Uploads the resized image to:

Bucket: dest_bucket (or DEST_BUCKET environment variable)

Key: the generated thumbnail key.

Return value (success):

json
Copy code
{
  "status": "SUCCESS",
  "source_bucket": "ccmp200-original-images-kahle",
  "source_key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "dest_key": "elepahnt_thumbnail.jpg",
  "width": 200,
  "height": 200
}
Return value (failure):

json
Copy code
{
  "status": "FAILED",
  "errorMessage": "...",
  "bucket": "...",
  "key": "..."
}
This structured result is used by Step Functions to decide whether to go to SuccessState or FailState.

6. Step Functions Workflow
File: state_machine_definition.json (exported from the console)

6.1 States
ResizeImage (Task)

Invokes resize-image-lambda with input fields:

bucket

key

dest_bucket

width

height

Stores Lambda output in $.resizeResult.

WasResizeSuccessful (Choice)

If $.resizeResult.status == "SUCCESS" → SuccessState

Otherwise → FailState

SuccessState (Succeed)

Marks the workflow as successfully completed.

FailState (Fail)

Marks the workflow as failed, with cause Image resize failed.

This provides clear pass/fail outcomes for the full workflow.

7. API Gateway Integration
7.1 Method Configuration
Method: POST /process-image

Integration type: AWS Service

Service: Step Functions

Action: StartExecution

Execution Role: IAM role that allows:

json
Copy code
{
  "Effect": "Allow",
  "Action": "states:StartExecution",
  "Resource": "arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine"
}
7.2 Mapping Template (application/json)
json
Copy code
{
  "input": "$util.escapeJavaScript($input.body)",
  "name": "$context.requestId",
  "stateMachineArn": "arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine"
}
input: passes the raw client JSON as the Step Functions input.

name: uses the API Gateway request ID as the execution name.

stateMachineArn: the ARN of ImageProcessingStateMachine.

8. Detailed Deployment Instructions
These steps assume a fresh deployment in ca-central-1.

8.1 Step 1 – Create S3 Buckets
Go to S3 → Create bucket.

Create bucket for originals:

Name: ccmp200-original-images-kahle

Create bucket for thumbnails:

Name: ccmp200-resized-images-kahle

Upload at least one test image (e.g., elepahnt.jpg) to the originals bucket.

8.2 Step 2 – Create the Lambda Function
Go to Lambda → Create function.

Name: resize-image-lambda.

Runtime: Python 3.11.

Use or create an execution role that allows:

s3:GetObject on ccmp200-original-images-kahle

s3:PutObject on ccmp200-resized-images-kahle

CloudWatch Logs permissions

In Configuration → Environment variables:

Add DEST_BUCKET = ccmp200-resized-images-kahle

In the Code tab:

Paste the contents of lambda_function.py.

Attach the Pillow Lambda layer:

Configuration → Layers → Add a layer

Select your Pillow layer (compatible with Python 3.11).

Test directly in Lambda using this event:

json
Copy code
{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}
Confirm that elepahnt_thumbnail.jpg appears in ccmp200-resized-images-kahle.

8.3 Step 3 – Create the Step Functions State Machine
Go to Step Functions → Create state machine.

Choose Author with code.

Paste the JSON from state_machine_definition.json, ensuring:

The Resource for the ResizeImage task is the Lambda ARN:

text
Copy code
arn:aws:lambda:ca-central-1:695085239748:function:resize-image-lambda
The state machine name is ImageProcessingStateMachine.

Let AWS create an execution role for Step Functions.

Save and test with:

json
Copy code
{
  "bucket": "ccmp200-original-images-kahle",
  "key": "elepahnt.jpg",
  "dest_bucket": "ccmp200-resized-images-kahle",
  "width": 200,
  "height": 200
}
Confirm the execution ends in SuccessState.

8.4 Step 4 – Create API Gateway REST API
Go to API Gateway → Create API → REST API (Build).

API name: ImageProcessingAPI.

Create a resource /process-image.

Under /process-image, add a POST method:

Integration type: AWS Service

AWS Service: Step Functions

HTTP method: POST

Action: StartExecution

Execution role: IAM role that allows states:StartExecution on:

text
Copy code
arn:aws:states:ca-central-1:695085239748:stateMachine:ImageProcessingStateMachine
In Integration Request → Mapping Templates:

Content-Type: application/json

Use the mapping template from Section 7.2.

8.5 Step 5 – Deploy API & Test
In API Gateway, click Actions → Deploy API.

Create or choose stage: prod.

Note the final URL:

text
Copy code
https://1etwk7h22i.execute-api.ca-central-1.amazonaws.com/prod/process-image
Test (Postman, curl, or API Gateway Test) with:

bash
Copy code
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

9. Testing & Validation
9.1 Unit-Level Test (Lambda)
Use the Lambda console with the example test event.

Confirm:

"status": "SUCCESS" in the response.

Thumbnail object created in ccmp200-resized-images-kahle.

9.2 Workflow Test (Step Functions)
Start an execution in the Step Functions console with the same JSON.

Confirm all states are green and the final state is SuccessState.

9.3 End-to-End Test (API)
Call the API Gateway URL (via curl, Postman, or the built-in Test tool).

Confirm:

HTTP 200 response with an executionArn.

New successful execution appears in Step Functions.

Thumbnail exists in the resized S3 bucket.

This demonstrates that the entire serverless image processing pipeline works as intended from HTTP request to resized image output.
