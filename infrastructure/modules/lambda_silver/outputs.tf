output "normalize_hn_arn" {
  description = "ARN of the normalize_hn Lambda function"
  value       = aws_lambda_function.normalize_hn.arn
}

output "normalize_hn_name" {
  description = "Name of the normalize_hn Lambda function"
  value       = aws_lambda_function.normalize_hn.function_name
}

output "normalize_twitter_arn" {
  description = "ARN of the normalize_twitter Lambda function"
  value       = aws_lambda_function.normalize_twitter.arn
}

output "normalize_twitter_name" {
  description = "Name of the normalize_twitter Lambda function"
  value       = aws_lambda_function.normalize_twitter.function_name
}