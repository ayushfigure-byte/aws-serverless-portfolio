# Lab 14: Enterprise Serverless RAG & Meteorological Knowledge Base

A serverless Retrieval-Augmented Generation (RAG) architecture using Amazon Bedrock Knowledge Bases, managed vector stores, and Amazon Nova Micro for grounding meteorological decision workflows in technical SOP documentation.

## Architecture Diagram
![Lab 14 Architecture](docs/architecture.png?v=1)

## Architecture & Design Patterns
1. **Managed Vector Storage & Ingestion:** Automated document chunking (300 tokens, 20% overlap) and vector embedding indexing from Amazon S3 into managed vector storage.
2. **Decoupled RAG Pipeline:** Separated vector similarity search (`bedrock-agent-runtime:retrieve`) from LLM synthesis (`bedrock-runtime:converse`), enabling granular prompt template control and model routing.
3. **Auditable Citations & Traceability:** Every generated recommendation binds directly to verifiable S3 source URIs, eliminating model hallucination in critical operational workflows.
4. **Low-Temperature Deterministic Inference:** Temperature set to 0.1 for high-fidelity compliance with official standard operating procedures.
