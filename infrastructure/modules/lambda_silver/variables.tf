variable "lambda_silver_role_arn" {
  description = "ARN of the IAM role for silver Lambda functions"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "normalize_hn_source_dir" {
  description = "Path to the normalize_hn Lambda source directory"
  type        = string
  default     = "../lambdas/normalize_hn"
}

variable "normalize_hn_output_path" {
  description = "Output path for the zipped normalize_hn Lambda package"
  type        = string
  default     = "../lambdas/normalize_hn.zip"
}

variable "normalize_twitter_source_dir" {
  description = "Path to the normalize_twitter Lambda source directory"
  type        = string
  default     = "../lambdas/normalize_twitter"
}

variable "normalize_twitter_output_path" {
  description = "Output path for the zipped normalize_twitter Lambda package"
  type        = string
  default     = "../lambdas/normalize_twitter.zip"
}

