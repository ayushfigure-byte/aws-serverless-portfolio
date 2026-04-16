Serverless Sentiment Inference Engine 🧠☁️
📌 Project Overview
As a Technical Product Manager, I designed and deployed this automated NLP (Natural Language Processing) pipeline to demonstrate how organizations can process unstructured customer feedback at scale. This project uses Event-Driven Architecture to eliminate the need for 24/7 server management, significantly reducing operational overhead.

🛠 Tech Stack
Infrastructure as Code: Terraform

Compute: AWS Lambda (Python 3.12)

AI/ML Service: Amazon Comprehend

Storage: Amazon S3 (Data Lake)

Security: IAM (Least Privilege Access)

📐 System Architecture
The system follows a reactive "Trigger-Action" pattern:

Ingestion: A .txt file is uploaded to the Input S3 Bucket.

Event Trigger: S3 sends a notification to AWS Lambda the millisecond the file is created.

Inference: Lambda calls the Amazon Comprehend API to analyze the sentiment (Positive, Negative, Neutral, or Mixed).

Storage: The JSON results, including confidence scores, are saved to the Output S3 Bucket.

Note: See architecture-diagram.png in this folder for the visual data flow.

📈 Technical PM Insights & Design Decisions
1. Cost Optimization (Pay-as-you-go)
By choosing a serverless stack, the total cost of this pipeline is nearly $0 at low volumes. We avoid the "Idle Server" cost entirely. For a business, this means the cost of sentiment analysis scales linearly with customer feedback volume, ensuring high ROI.

2. Security (Zero Trust / Least Privilege)
I implemented a granular IAM policy that restricts the Lambda's permissions. Unlike a "FullAccess" approach, this function can only read from the input bucket and write to the output bucket, minimizing the blast radius of any potential security incident.

3. Scalability
Because AWS Lambda is inherently scalable, this pipeline can process 1 file or 10,000 files simultaneously without any manual capacity planning or infrastructure changes.

🚀 Deployment Instructions
To replicate this environment:

Initialize Terraform: terraform init

Review the plan: terraform plan

Deploy: terraform apply

Test by uploading a .txt file to the created input bucket.
