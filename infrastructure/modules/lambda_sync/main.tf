data "aws_region" "current" {}

locals {
  awswrangler_layer_arn = "arn:aws:lambda:${data.aws_region.current.name}:336392948345:layer:AWSSDKPandas-Python312:18"
}

data "archive_file" "lambda_sync" {
  type        = "zip"
  source_dir  = var.lambda_sync_source_dir
  output_path = var.lambda_sync_output_path
}

resource "aws_lambda_function" "lambda_sync" {
  filename         = data.archive_file.lambda_sync.output_path
  function_name    = "lambda_sync"
  handler          = "handler.handler"
  runtime          = "python3.12"
  role             = var.lambda_sync_role_arn
  timeout          = 300
  memory_size      = 512
  source_code_hash = data.archive_file.lambda_sync.output_base64sha256
  layers           = [local.awswrangler_layer_arn]
  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }
  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
      DB_HOST     = var.db_host
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
    }
  }
}
