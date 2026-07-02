variable "step_function_role_arn" {
  description = "ARN of the IAM role the Step Functions state machine assumes (from modules/iam)"
  type        = string
}

variable "bronze_lambda_arn" {
  description = "ARN of the bronze_layer Lambda function"
  type        = string
}

variable "normalize_hn_lambda_arn" {
  description = "ARN of the normalize_hn Lambda function"
  type        = string
}

variable "gold_lambda_arn" {
  description = "ARN of the gold Lambda function"
  type        = string
}

variable "lambda_sync_lambda_arn" {
  description = "ARN of the lambda_sync Lambda function"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge cron/rate expression that triggers the whole pipeline daily"
  type        = string
  default     = "cron(0 1 * * ? *)"
}