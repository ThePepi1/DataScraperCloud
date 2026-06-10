output "lambda_arn" {
  description = "ARN of the bronze layer Lambda function"
  value       = aws_lambda_function.bronze_layer.arn
}

output "lambda_name" {
  description = "Name of the bronze layer Lambda function"
  value       = aws_lambda_function.bronze_layer.function_name
}
