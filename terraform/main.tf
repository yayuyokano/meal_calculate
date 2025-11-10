terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC とネットワーク設定は既存のものを参照
data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_subnet" "subnet_1" {
  id = var.subnet_1_id
}

data "aws_subnet" "subnet_2" {
  id = var.subnet_2_id
}


data "aws_security_group" "app" {
  id = var.security_group_id
}
