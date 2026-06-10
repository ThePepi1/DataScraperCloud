variable "lambda_gold_role_arn" {
  type = string
}

variable "s3_bucket_name" {
  type = string
}

variable "gold_source_dir" {
  type    = string
  default = "../lambdas/gold"
}

variable "gold_output_path" {
  type    = string
  default = "../lambdas/gold.zip"
}