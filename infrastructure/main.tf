terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "eu-central-1"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

module "s3" {
  source = "./modules/s3"
}

module "vpc" {
  source = "./modules/vpc"
}

module "iam" {
  source         = "./modules/iam"
  s3_bucket_arn  = module.s3.bucket_arn
}

module "lambda" {
  source          = "./modules/lambda"
  lambda_role_arn = module.iam.lambda_role_arn
  s3_bucket_name  = module.s3.bucket_name
}

module "eventbridge" {
  source               = "./modules/eventbridge"
  lambda_function_arn  = module.lambda.lambda_arn
  lambda_function_name = module.lambda.lambda_name
}
module "lambda_silver" {
  source                 = "./modules/lambda_silver"
  lambda_silver_role_arn = module.iam.lambda_silver_role_arn
  s3_bucket_name         = module.s3.bucket_name
}
module "discord_notifier" {
  source = "./modules/discord_notifier"

  lambda_role_arn     = module.iam.discord_notifier_role_arn
  discord_webhook_url = var.discord_webhook_url
}
module "lambda_gold" {
  source = "./modules/lambda_gold"
  lambda_gold_role_arn = module.iam.lambda_gold_role_arn
  s3_bucket_name       = module.s3.bucket_name
}
