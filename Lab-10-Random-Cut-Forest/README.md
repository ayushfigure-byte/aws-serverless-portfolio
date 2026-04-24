# Lab 10: Tactical Anomaly Detection with SageMaker RCF

## Overview
This lab implements a real-time MLOps pipeline to detect performance anomalies in tactical athletes. It uses a **Random Cut Forest (RCF)** algorithm to identify heart rate/pace deviations that could indicate overtraining or medical distress.

## Architecture
![Architecture Diagram](./images/architecture.png)

1. **Ingestion:** Raw workout data is sent to **Amazon SQS**.
2. **Storage:** A Python Lambda processes the queue and vaults data into **DynamoDB**.
3. **Trigger:** **DynamoDB Streams** emit events for every new workout recorded.
4. **Inference:** The **Anomaly Scout Lambda** extracts features and calls a **SageMaker Endpoint**.
5. **Alerting:** Anomalies with a score > 2.0 are flagged in **CloudWatch Logs**.

## Key Concepts
- **Asynchronous Decoupling:** Using SQS ensures the system can scale to thousands of athletes without dropping data.
- **Event-Driven AI:** The model only runs when new data arrives, minimizing compute costs.
