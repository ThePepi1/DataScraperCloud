variable "lambda_role_arn" {
  description = "ARN of the IAM role for the Discord notifier Lambda"
  type        = string
}

variable "discord_webhook_url" {
  description = "Discord Incoming Webhook URL (store in SSM or pass via tfvars — never hardcode)"
  type        = string
  sensitive   = true
}

variable "lambda_source_dir" {
  description = "Path to the Discord notifier Lambda source directory"
  type        = string
  default     = "../lambdas/discord-notifier"
}

variable "lambda_output_path" {
  description = "Output path for the zipped Lambda package"
  type        = string
  default     = "../lambdas/discord-notifier.zip"
}
