output "lambda_sync_arn" {
  description = "Lambda sync function ARN"
  value       = aws_lambda_function.lambda_sync.arn
}

output "lambda_sync_name" {
  description = "Lambda sync function naziv"
  value       = aws_lambda_function.lambda_sync.function_name
}