# 1. Define the Cloud Provider
provider "aws" {
  region = "us-east-1"
}

# 2. Create the Dead Letter Queue (The Safety Net)
resource "aws_sqs_queue" "ticket_dlq" {
  name                      = "ticket-processing-dlq"
  message_retention_seconds = 1209600 # Hold failed messages for 14 days for PM review
}

# 3. Create the Main SQS Queue
resource "aws_sqs_queue" "main_ticket_queue" {
  name                      = "high-volume-ticket-queue"
  delay_seconds             = 0
  max_message_size          = 262144 # 256 KB max payload
  message_retention_seconds = 86400  # Hold unprocessed messages for 1 day
  receive_wait_time_seconds = 10     # Enable Long Polling (Reduces AWS Costs)

  # 4. The API Contract: Connect the Main Queue to the DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ticket_dlq.arn
    maxReceiveCount     = 3 # If Lambda fails 3 times, move it to the DLQ
  })
}
