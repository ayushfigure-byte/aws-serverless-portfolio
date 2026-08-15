# Lab 12: Event-Driven GenAI Weather Advisory Engine

An event-driven alerting system that consumes DynamoDB Streams CDC events, prompts Amazon Bedrock (Nova Micro) via the Converse API for domain risk impact analysis, and broadcasts notifications using Amazon SNS.

## Architecture
1. **Amazon DynamoDB Streams:** Emits CDC records on anomaly insertion (`INSERT`).
2. **AWS Lambda (Python 3.12):** Unmarshalls DynamoDB JSON and orchestrates LLM inference.
3. **Amazon Bedrock (`amazon.nova-micro-v1:0`):** Synthesizes natural language risk assessments covering energy grids, aviation, and public safety.
4. **Amazon SNS:** Distributes formatted advisories to multi-channel subscribers.
