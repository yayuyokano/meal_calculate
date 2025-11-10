variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "meal-calculate"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_1_id" {
  description = "Subnet 1 ID"
  type        = string
}

variable "subnet_2_id" {
  description = "Subnet 2 ID"
  type        = string
}

variable "security_group_id" {
  description = "Security Group ID"
  type        = string
}

variable "github_repo_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "yayuyokano"
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "meal_calculate"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "github_oauth_token" {
  description = "GitHub OAuth token for CodePipeline"
  type        = string
  sensitive   = true
}

variable "github_webhook_secret" {
  description = "GitHub webhook secret"
  type        = string
  sensitive   = true
}
