output "discord_notifier_arn" {
  description = "ARN of the Discord notifier Lambda"
  value       = aws_lambda_function.discord_notifier.arn
}

output "discord_notifier_name" {
  description = "Name of the Discord notifier Lambda"
  value       = aws_lambda_function.discord_notifier.function_name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for Lambda failures"
  value       = aws_cloudwatch_event_rule.job_failures.arn
}
