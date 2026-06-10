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

  timeout     = 900
  memory_size = 1024

  source_code_hash = data.archive_file.gold_lambda.output_base64sha256

  layers = [local.awswrangler_layer_arn]

  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}


resource "aws_cloudwatch_event_rule" "gold_daily" {
  name                = "gold-daily"
  schedule_expression = "cron(0 19 * * ? *)"
}

resource "aws_cloudwatch_event_target" "gold_target" {
  rule      = aws_cloudwatch_event_rule.gold_daily.name
  target_id = "gold"
  arn       = aws_lambda_function.gold.arn
}

resource "aws_lambda_permission" "gold_eventbridge" {
  statement_id  = "AllowEventBridgeInvokeGold"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gold.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.gold_daily.arn
}