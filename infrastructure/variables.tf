variable "aws_access_key" {
  type      = string
  sensitive = true
}

variable "aws_secret_key" {
  type      = string
  sensitive = true
}
variable "discord_webhook_url" {
  description = "Discord Incoming Webhook URL — nikad ne hardcode-uj, koristi tfvars ili SSM"
  type        = string
  sensitive   = true
}
