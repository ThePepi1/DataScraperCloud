
data "archive_file" "discord_notifier" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = var.lambda_output_path
}

resource "aws_lambda_function" "discord_notifier" {
  function_name    = "discord-notifier"
  description      = "Sends Discord notifications when AWS jobs fail (Lambda, Glue, Step Functions)"
  role             = var.lambda_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.discord_notifier.output_path
  source_code_hash = data.archive_file.discord_notifier.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      DISCORD_WEBHOOK_URL = var.discord_webhook_url
    }
  }

  tags = {
    Purpose = "discord-notifications"
  }
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.discord_notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.job_failures.arn
}


resource "aws_cloudwatch_event_rule" "job_failures" {
  name        = "aws-job-failures"
  description = "Catches failed jobs from Lambda, Glue and Step Functions"

  event_pattern = jsonencode({
    "$or" = [
      {
        source      = ["aws.lambda"]
        detail-type = ["Lambda Function Invocation Result - Failure"]
      },
      {
        source      = ["aws.glue"]
        detail-type = ["Glue Job State Change"]
        detail = {
          state = ["FAILED", "TIMEOUT", "ERROR"]
        }
      },
      {
        source      = ["aws.states"]
        detail-type = ["Step Functions Execution Status Change"]
        detail = {
          status = ["FAILED", "TIMED_OUT", "ABORTED"]
        }
      }
    ]
  })
}

resource "aws_cloudwatch_event_target" "discord_notifier" {
  rule      = aws_cloudwatch_event_rule.job_failures.name
  target_id = "discord-notifier-lambda"
  arn       = aws_lambda_function.discord_notifier.arn
}
