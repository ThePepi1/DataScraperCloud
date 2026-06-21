data "aws_region" "current" {}

locals {
  awswrangler_layer_arn = "arn:aws:lambda:${data.aws_region.current.name}:336392948345:layer:AWSSDKPandas-Python312:18"
}

data "archive_file" "gold_lambda" {
  type        = "zip"
  source_dir  = var.gold_source_dir
  output_path = var.gold_output_path
}

resource "aws_lambda_function" "gold" {
  filename         = data.archive_file.gold_lambda.output_path
  function_name    = "gold_lambda"
  handler          = "handler.handler"
  runtime          = "python3.12"
  role             = var.lambda_gold_role_arn
  timeout          = 900
  memory_size      = 1024
  source_code_hash = data.archive_file.gold_lambda.output_base64sha256
  layers           = [local.awswrangler_layer_arn]
  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}

