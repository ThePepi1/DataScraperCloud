output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_bronze.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda IAM role"
  value       = aws_iam_role.lambda_bronze.name
}
output "lambda_silver_role_arn" {
  description = "ARN of the silver Lambda IAM role"
  value       = aws_iam_role.lambda_silver.arn
}

output "lambda_silver_role_name" {
  description = "Name of the silver Lambda IAM role"
  value       = aws_iam_role.lambda_silver.name
}
output "discord_notifier_role_arn" {
  description = "ARN of the Discord notifier Lambda role"
  value       = aws_iam_role.discord_notifier_role.arn
}

output "discord_notifier_role_name" {
  description = "Name of the Discord notifier Lambda role"
  value       = aws_iam_role.discord_notifier_role.name
}
output "lambda_gold_role_arn" {
  value = aws_iam_role.lambda_gold.arn
}
output "lambda_sync_role_arn" {
  description = "ARN of the sync Lambda IAM role"
  value       = aws_iam_role.lambda_sync.arn
}