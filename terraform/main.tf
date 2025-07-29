provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "lambda_ecr_repo" {
  name = "${var.lambda_function_name}-repo"
  
  tags = {
    Name = "Lambda ECR Repository"
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name               = "cost-anomaly-detection-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_exec_policy" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    actions   = ["ce:GetCostAndUsage"]
    resources = ["*"]
  }

  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.slack_bot_token.arn]
  }

  statement {
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability"
    ]
    resources = [aws_ecr_repository.lambda_ecr_repo.arn]
  }

  statement {
    actions   = ["bedrock:InvokeModel"]
    resources = ["*"] # Or you can restrict to specific model ARNs
  }
}

resource "aws_iam_role_policy" "lambda_exec_policy" {
  name   = "cost-anomaly-detection-lambda-exec-policy"
  role   = aws_iam_role.lambda_exec_role.id
  policy = data.aws_iam_policy_document.lambda_exec_policy.json
}

resource "aws_ssm_parameter" "slack_bot_token" {
  name  = "CostAnomalyDetectionSlackBotToken"
  type  = "SecureString"
  value = var.slack_bot_token
}

resource "aws_lambda_function" "cost_anomaly_detector" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 300 # Increased timeout for ML model
  memory_size   = 1024 # Increased memory for ML model
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_ecr_repo.repository_url}:latest"

  environment {
    variables = {
      SLACK_TOKEN_PARAMETER_NAME = aws_ssm_parameter.slack_bot_token.name
      SLACK_CHANNEL              = var.slack_channel
    }
  }
}

resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "daily-cost-anomaly-trigger"
  description         = "Triggers the cost anomaly detector Lambda daily"
  schedule_expression = "cron(0 12 * * ? *)" # Trigger every day at 12:00 PM UTC
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "CostAnomalyDetectorLambda"
  arn       = aws_lambda_function.cost_anomaly_detector.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_anomaly_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
} 