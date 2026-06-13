variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_id" {
  description = "Public subnet ID"
  type        = string
}

variable "lambda_sg_id" {
  description = "Lambda security group ID"
  type        = string
}

variable "my_ip" {
  description = "Lista dozvoljenih IP adresa"
  type        = list(string)
}

variable "ec2_ami" {
  description = "Ubuntu 22.04 AMI za eu-central-1"
  type        = string
  default     = "ami-0faab6bdbac9486fb"
}

variable "ec2_instance_type" {
  description = "EC2 tip instance"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Naziv SSH key pair-a iz AWS konzole"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL lozinka"
  type        = string
  sensitive   = true
}

variable "superset_secret_key" {
  description = "Superset secret key"
  type        = string
  sensitive   = true
}

variable "superset_admin_password" {
  description = "Superset admin lozinka"
  type        = string
  sensitive   = true
}

variable "superset_admin_username" {
  description = "Superset admin username"
  type        = string
  default     = "admin"
}

variable "superset_admin_firstname" {
  description = "Superset admin first name"
  type        = string
  default     = "Admin"
}

variable "superset_admin_lastname" {
  description = "Superset admin last name"
  type        = string
  default     = "Admin"
}

variable "superset_admin_email" {
  description = "Superset admin email"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}