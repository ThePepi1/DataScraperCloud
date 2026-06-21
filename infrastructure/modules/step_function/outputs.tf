output "state_machine_arn" {
  description = "ARN of the data pipeline Step Functions state machine"
  value       = aws_sfn_state_machine.data_pipeline.arn
}

output "state_machine_name" {
  description = "Name of the data pipeline Step Functions state machine"
  value       = aws_sfn_state_machine.data_pipeline.name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule that triggers the pipeline daily"
  value       = aws_cloudwatch_event_rule.pipeline_daily.arn
}
