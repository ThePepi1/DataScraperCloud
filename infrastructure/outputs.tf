output "s3_bucket_name" {
  description = "The name of the data lake S3 bucket"
  value       = module.s3.bucket_name
}

output "lambda_function_name" {
  description = "The name of the bronze layer Lambda function"
  value       = module.lambda.lambda_name
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}
