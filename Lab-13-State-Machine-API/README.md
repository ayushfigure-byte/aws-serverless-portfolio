# Lab 13: Enterprise State Machine Orchestration & Advisory API Engine

An enterprise serverless API and orchestration layer combining Amazon API Gateway, AWS Step Functions (Standard Workflow), Amazon DynamoDB caching, and Amazon Bedrock (Nova Micro) resilience patterns.

## Architecture Diagram
![Lab 13 Architecture](docs/architecture.png?v=1)

## Architecture & Design Patterns
1. **Direct AWS Service Integrations:** API Gateway integrates directly with Step Functions (`StartExecution`), and Step Functions communicates directly with DynamoDB (`GetItem`/`PutItem`), Bedrock (`InvokeModel`), and SNS (`Publish`) without intermediary Lambda functions.
2. **Write-Through Semantic Caching:** Implements a DynamoDB cache layer to short-circuit duplicate queries, achieving sub-100ms response times and eliminating unnecessary LLM token spend.
3. **Resilience & Fault Tolerance:** Configured automated exponential backoff retries on Bedrock model throttling (`Bedrock.ThrottlingException`) directly inside the ASL state definition.
4. **Conditional Escalation Routing:** Choice states evaluate anomaly metrics ($z \ge 2.5\sigma$) to conditionally broadcast alerts to operations teams via Amazon SNS.
