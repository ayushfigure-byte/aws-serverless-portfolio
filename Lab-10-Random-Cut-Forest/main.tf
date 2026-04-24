# 1. THE INFRASTRUCTURE (SQS & DYNAMODB)
resource "aws_sqs_queue" "training_queue" {
  name = "tactical-training-queue"
}

resource "aws_dynamodb_table" "training_history" {
  name             = "T3-Training-History"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "AthleteID"
  range_key        = "Timestamp"
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute { name = "AthleteID"; type = "S" }
  attribute { name = "Timestamp"; type = "S" }
}

# 2. THE SECURITY (IAM ROLE & POLICY)
resource "aws_iam_role" "t3_lambda_role" {
  name = "t3_lambda_master_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "t3_master_policy" {
  name = "t3_lambda_master_policy"
  role = aws_iam_role.t3_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.training_queue.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetRecords", "dynamodb:GetShardIterator", "dynamodb:DescribeStream", "dynamodb:ListStreams"]
        Resource = [aws_dynamodb_table.training_history.arn, "${aws_dynamodb_table.training_history.arn}/stream/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["sagemaker:InvokeEndpoint"]
        Resource = "*" # Allows calling your RCF model
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# 3. THE FUNCTIONS (LAMBDAS)
resource "aws_lambda_function" "processor" {
  filename      = "processor.zip"
  function_name = "T3-Data-Processor"
  role          = aws_iam_role.t3_lambda_role.arn
  handler       = "processor.lambda_handler"
  runtime       = "python3.9"
}

resource "aws_lambda_function" "scout" {
  filename      = "scout.zip"
  function_name = "T3-RCF-Anomaly-Scout"
  role          = aws_iam_role.t3_lambda_role.arn
  handler       = "scout.lambda_handler"
  runtime       = "python3.9"

  environment {
    variables = {
      ENDPOINT_NAME = "randomcutforest-2026-04-23-13-11-19-345" # Update this after training
    }
  }
}

# 4. THE TRIGGERS (EVENT SOURCE MAPPINGS)
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.training_queue.arn
  function_name    = aws_lambda_function.processor.arn
}

resource "aws_lambda_event_source_mapping" "dynamodb_trigger" {
  event_source_arn  = aws_dynamodb_table.training_history.stream_arn
  function_name     = aws_lambda_function.scout.arn
  starting_position = "LATEST"
}
