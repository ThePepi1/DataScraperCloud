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
  my_ip  = var.my_ip
  vpc_cidr = var.vpc_cidr
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
module "ec2" {
  source = "./modules/ec2"

  vpc_id    = module.vpc.vpc_id
  subnet_id = module.vpc.public_subnet_id
  lambda_sg_id = module.vpc.lambda_sg_id
  my_ip     = var.my_ip
  vpc_cidr  = var.vpc_cidr

  key_pair_name            = var.key_pair_name
  db_password              = var.db_password
  superset_secret_key      = var.superset_secret_key
  superset_admin_password  = var.superset_admin_password
  superset_admin_username  = var.superset_admin_username
  superset_admin_firstname = var.superset_admin_firstname
  superset_admin_lastname  = var.superset_admin_lastname
  superset_admin_email     = var.superset_admin_email
}
module "lambda_sync" {
  source = "./modules/lambda_sync"

  lambda_sync_role_arn = module.iam.lambda_sync_role_arn
  s3_bucket_name       = module.s3.bucket_name
  db_host              = module.ec2.db_endpoint
  db_password          = var.db_password
  subnet_ids           = [module.vpc.public_subnet_id]
  lambda_sg_id         = module.vpc.lambda_sg_id
}