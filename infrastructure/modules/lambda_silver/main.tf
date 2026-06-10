data "aws_region" "current" {}

locals {
  awswrangler_layer_arn = "arn:aws:lambda:${data.aws_region.current.name}:336392948345:layer:AWSSDKPandas-Python312:18"
}

data "archive_file" "normalize_hn" {
  type        = "zip"
  source_dir  = var.normalize_hn_source_dir
  output_path = var.normalize_hn_output_path
}

resource "aws_lambda_function" "normalize_hn" {
  filename         = data.archive_file.normalize_hn.output_path
  function_name    = "normalize_hn_lambda"
  handler          = "handler.handler"
  runtime          = "python3.12"
  role             = var.lambda_silver_role_arn
  timeout          = 300
  memory_size      = 512
  source_code_hash = data.archive_file.normalize_hn.output_base64sha256

  layers = [local.awswrangler_layer_arn]

  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_permission" "normalize_hn_s3" {
  statement_id  = "AllowS3InvokeNormalizeHN"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.normalize_hn.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_bucket_name}"
}

data "archive_file" "normalize_twitter" {
  type        = "zip"
  source_dir  = var.normalize_twitter_source_dir
  output_path = var.normalize_twitter_output_path
}

resource "aws_lambda_function" "normalize_twitter" {
  filename         = data.archive_file.normalize_twitter.output_path
  function_name    = "normalize_twitter_lambda"
  handler          = "handler.handler"
  runtime          = "python3.12"
  role             = var.lambda_silver_role_arn
  timeout          = 300
  memory_size      = 1024
  source_code_hash = data.archive_file.normalize_twitter.output_base64sha256

  layers = [local.awswrangler_layer_arn]

  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_permission" "normalize_twitter_s3" {
  statement_id  = "AllowS3InvokeNormalizeTwitter"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.normalize_twitter.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_bucket_name}"
}

resource "aws_s3_bucket_notification" "silver_triggers" {
  bucket = var.s3_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.normalize_hn.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "bronze/hackernews/"
    filter_suffix       = ".json"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.normalize_twitter.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "bronze/twitter/"
    filter_suffix       = ".csv"
  }

  depends_on = [
    aws_lambda_permission.normalize_hn_s3,
    aws_lambda_permission.normalize_twitter_s3,
  ]
}