variable "lambda_sync_role_arn" {
  description = "IAM role ARN za lambda sync"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket naziv"
  type        = string
}

variable "db_host" {
  description = "PostgreSQL host (EC2 private IP)"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL lozinka"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "PostgreSQL baza"
  type        = string
  default     = "gold_db"
}

variable "db_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "superset"
}

variable "subnet_ids" {
  description = "Subnet IDs za Lambda VPC config"
  type        = list(string)
}

variable "lambda_sg_id" {
  description = "Lambda security group ID"
  type        = string
}

variable "lambda_sync_source_dir" {
  description = "Path do lambda_sync source koda"
  type        = string
    default = "../lambdas/sync"
}

variable "lambda_sync_output_path" {
  description = "Path za zip output"
  type        = string
  default     = "../lambdas/sync.zip"
}