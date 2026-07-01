output "ec2_public_ip" {
  description = "Javna IP adresa EC2 instance"
  value       = aws_instance.superset.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.superset.id
}

output "db_endpoint" {
  description = "PostgreSQL private IP za Lambda sync"
  value       = aws_instance.superset.private_ip
}

output "ec2_sg_id" {
  description = "EC2 security group ID"
  value       = aws_security_group.ec2.id
}