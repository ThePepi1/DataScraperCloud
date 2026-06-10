variable "lambda_function_arn" {
  description = "ARN of the Lambda function to trigger"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to trigger"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge cron or rate schedule expression"
  type        = string
  default     = "cron(0 1 * * ? *)"
}
