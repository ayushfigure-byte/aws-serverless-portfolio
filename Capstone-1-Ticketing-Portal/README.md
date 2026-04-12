Capstone 1: Serverless IT Support Portal

## Architecture Overview
This project is a fully decoupled serverless web application built on AWS. 

![System Architecture](Serverless%20Website%20Ticketing%20Architecture.drawio.png)

## The Tech Stack
* **Frontend:** Amazon S3 (Static Web Hosting)
* **Routing & Security:** Amazon API Gateway (Lambda Proxy Integration)
* **Compute / Backend:** AWS Lambda (Python)
* **Database:** Amazon DynamoDB (NoSQL)

## The API Contract
The system enforces a strict schema for incoming payloads. API Gateway acts as the first line of defense, returning a `400 Bad Request` if the frontend fails to provide the required fields, protecting the database from malformed data.
