variable "lambda_role_arn" {
  description = "ARN of the IAM role for the Lambda function"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket passed as an environment variable"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for VPC config"
  type        = list(string)
  default = [  ]
}

variable "security_group_ids" {
  description = "List of security group IDs for VPC config"
  type        = list(string)
  default = [  ]
}

variable "lambda_source_dir" {
  description = "Path to the Lambda source directory"
  type        = string
  default     = "../lambdas/bronze-layer"
}

variable "lambda_output_path" {
  description = "Output path for the zipped Lambda package"
  type        = string
  default     = "../lambdas/bronze-layer.zip"
}
