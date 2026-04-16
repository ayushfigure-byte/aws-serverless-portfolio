terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_iam_role" "lambda_exec" {
  name = "sentiment_analysis_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_comprehend" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/ComprehendReadOnly"
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
# 1. Create a random suffix for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# 2. Input Bucket (Raw Text)
resource "aws_s3_bucket" "input_bucket" {
  bucket        = "sentiment-input-ayush-${random_id.bucket_suffix.hex}"
  force_destroy = true 
}

# 3. Output Bucket (Processed Results)
resource "aws_s3_bucket" "output_bucket" {
  bucket        = "sentiment-output-ayush-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

# 4. Useful Outputs
output "input_bucket_name" {
  value = aws_s3_bucket.input_bucket.id
}

output "output_bucket_name" {
  value = aws_s3_bucket.output_bucket.id
}
# 1. The Lambda Function Resource
resource "aws_lambda_function" "sentiment_processor" {
  filename      = "lambda_function_payload.zip"
  function_name = "sentiment_inference_engine"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_function.lambda_handler" # File name . Function name
  runtime       = "python3.12"

  environment {
    variables = {
      OUTPUT_BUCKET = aws_s3_bucket.output_bucket.id
    }
  }
}

# 2. Permission for S3 to "Call" the Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sentiment_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.input_bucket.arn
}

# 3. The Actual Trigger (The "Event Bridge")
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.input_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.sentiment_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "lambda_s3_access_policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject", "s3:PutObject"]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.input_bucket.arn}/*",
          "${aws_s3_bucket.output_bucket.arn}/*"
        ]
      }
    ]
  })
}
