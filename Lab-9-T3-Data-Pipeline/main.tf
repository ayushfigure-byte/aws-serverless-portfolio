# --- 1. Provider & Network ---
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "t3_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "T3-Tactical-VPC" }
}

resource "aws_subnet" "t3_public_subnet" {
  vpc_id     = aws_vpc.t3_vpc.id
  cidr_block = "10.0.1.0/24"
  tags       = { Name = "T3-Public-Subnet" }
}

# --- 2. Ingestion (SQS) ---
resource "aws_sqs_queue" "t3_training_queue" {
  name = "tactical-training-queue"
}

# --- 3. Storage (DynamoDB) ---
resource "aws_dynamodb_table" "t3_history" {
  name         = "T3-Training-History"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "AthleteID"
  range_key    = "TrainingTimestamp"

  attribute { name = "AthleteID"; type = "S" }
  attribute { name = "TrainingTimestamp"; type = "S" }
}

# --- 4. Compute (Lambda) ---
resource "aws_iam_role" "t3_lambda_role" {
  name = "t3_lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs" {
  role       = aws_iam_role.t3_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_iam_policy" "lambda_dynamodb" {
  name = "t3_lambda_dynamodb_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem"]
      Resource = [aws_dynamodb_table.t3_history.arn]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_db_attach" {
  role       = aws_iam_role.t3_lambda_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb.arn
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "process_data.py"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "t3_processor" {
  filename         = "lambda_function.zip"
  function_name    = "T3-Data-Processor"
  role             = aws_iam_role.t3_lambda_role.arn
  handler          = "process_data.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.t3_training_queue.arn
  function_name    = aws_lambda_function.t3_processor.arn
}
