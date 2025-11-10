# CodePipeline for Terraform Infrastructure Updates

# IAM Role for Terraform Pipeline
resource "aws_iam_role" "terraform_pipeline" {
  name = "${var.project_name}-terraform-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "${var.project_name}-terraform-pipeline-role"
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "terraform_pipeline" {
  role = aws_iam_role.terraform_pipeline.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.terraform_state.arn}/*",
          "${aws_s3_bucket.codepipeline.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          aws_s3_bucket.codepipeline.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = aws_codebuild_project.terraform.arn
      }
    ]
  })
}

# Manual Approval SNS Topic
resource "aws_sns_topic" "terraform_approval" {
  name = "${var.project_name}-terraform-approval"

  tags = {
    Name    = "${var.project_name}-terraform-approval"
    Project = var.project_name
  }
}

# CodePipeline for Terraform
resource "aws_codepipeline" "terraform" {
  name     = "${var.project_name}-terraform-pipeline"
  role_arn = aws_iam_role.terraform_pipeline.arn

  artifact_store {
    location = aws_s3_bucket.terraform_state.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["SourceArtifact"]

      configuration = {
        Owner                = var.github_repo_owner
        Repo                 = var.github_repo_name
        Branch               = "main"
        OAuthToken           = var.github_oauth_token
        PollForSourceChanges = false
      }
    }
  }

  stage {
    name = "Plan"

    action {
      name             = "TerraformPlan"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["SourceArtifact"]
      output_artifacts = ["PlanArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.terraform.name
      }
    }
  }

  stage {
    name = "Approval"

    action {
      name     = "ManualApproval"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"

      configuration = {
        NotificationArn = aws_sns_topic.terraform_approval.arn
        CustomData      = "Please review Terraform plan and approve infrastructure changes."
      }
    }
  }

  stage {
    name = "Apply"

    action {
      name            = "TerraformApply"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["PlanArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.terraform.name
      }
    }
  }

  tags = {
    Name    = "${var.project_name}-terraform-pipeline"
    Project = var.project_name
  }
}

# Webhook for Terraform Pipeline
resource "aws_codepipeline_webhook" "terraform" {
  name            = "${var.project_name}-terraform-webhook"
  target_pipeline = aws_codepipeline.terraform.name
  target_action   = "Source"
  authentication  = "GITHUB_HMAC"

  authentication_configuration {
    secret_token = var.github_webhook_secret
  }

  filter {
    json_path    = "$.ref"
    match_equals = "refs/heads/main"
  }

  # Only trigger on terraform directory changes
  filter {
    json_path    = "$.commits[*].modified[*]"
    match_equals = "terraform/*"
  }

  tags = {
    Name    = "${var.project_name}-terraform-webhook"
    Project = var.project_name
  }
}

output "terraform_pipeline_name" {
  description = "Terraform CodePipeline name"
  value       = aws_codepipeline.terraform.name
}

output "terraform_approval_topic" {
  description = "SNS topic for Terraform approval notifications"
  value       = aws_sns_topic.terraform_approval.arn
}
