# T3 Tactical Anomaly Detection Infrastructure
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

# (Lambdas and IAM Roles would follow here - using the logic we debugged)
