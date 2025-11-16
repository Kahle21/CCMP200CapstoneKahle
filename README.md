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
