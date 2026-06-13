resource "aws_security_group" "ec2" {
  name   = "ec2-superset-sg"
  vpc_id = var.vpc_id

ingress {
  description = "SSH"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = [for ip in var.my_ip : "${ip}/32"]
}

ingress {
  description = "Superset UI"
  from_port   = 8088
  to_port     = 8088
  protocol    = "tcp"
  cidr_blocks = [for ip in var.my_ip : "${ip}/32"]
}

  ingress {
    description     = "PostgreSQL samo od Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.lambda_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ec2-superset-sg"
  }
}

resource "aws_iam_role" "ec2_role" {
  name = "superset-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "superset-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "superset" {
  ami                    = var.ec2_ami
  instance_type          = var.ec2_instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  key_name               = var.key_pair_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }
   credit_specification {
    cpu_credits = "standard"
  }

  user_data = templatefile("${path.module}/scripts/setup.sh.tpl", {
    db_password              = var.db_password
    superset_secret_key      = var.superset_secret_key
    superset_admin_password  = var.superset_admin_password
    superset_admin_username  = var.superset_admin_username
    superset_admin_firstname = var.superset_admin_firstname
    superset_admin_lastname  = var.superset_admin_lastname
    superset_admin_email     = var.superset_admin_email
    vpc_cidr                 = var.vpc_cidr
  })

  tags = {
    Name = "superset-ec2"
  }
}