resource "aws_cloudwatch_event_rule" "bronze_hn_daily" {
  name                = "bronze-hn-daily-trigger"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "bronze_hn" {
  rule      = aws_cloudwatch_event_rule.bronze_hn_daily.name
  target_id = "bronze-hn-lambda"
  arn       = var.lambda_function_arn
}

resource "aws_lambda_permission" "eventbridge_bronze_hn" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bronze_hn_daily.arn
}
