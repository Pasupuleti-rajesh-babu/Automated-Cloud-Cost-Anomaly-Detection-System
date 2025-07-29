variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "slack_bot_token" {
  description = "The Slack bot token for sending alerts."
  type        = string
  sensitive   = true
}

variable "slack_channel" {
  description = "The Slack channel to send alerts to (e.g., #general)."
  type        = string
  default     = "#general"
}

variable "lambda_function_name" {
  description = "The name of the Lambda function."
  type        = string
  default     = "cost-anomaly-detector"
} 