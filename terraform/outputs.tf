output "ecr_repository_url" {
  description = "The URL of the ECR repository for the Lambda function."
  value       = aws_ecr_repository.lambda_ecr_repo.repository_url
}

output "lambda_iam_role_arn" {
  description = "The ARN of the IAM role used by the Lambda function."
  value       = aws_iam_role.lambda_exec_role.arn
}

output "lambda_function_name" {
  description = "The name of the created Lambda function."
  value       = aws_lambda_function.cost_anomaly_detector.function_name
} 