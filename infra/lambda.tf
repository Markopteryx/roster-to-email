resource "aws_iam_role" "lambda_execution_role" {
  name = "ShiftsLambdaExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_combined_policy" {
  name = "ShiftsLambdaPolicy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "ses:SendRawEmail"
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_ecr_image" "service_image" {
  repository_name = aws_ecr_repository.lambda_repository.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "lambda_function" {
  function_name = "Shifts"

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda_repository.repository_url}@${data.aws_ecr_image.service_image.image_digest}"

  role        = aws_iam_role.lambda_execution_role.arn
  memory_size = 2048
  timeout     = 30

  environment {
    variables = {
      TO_EMAIL        = data.aws_ssm_parameter.to_email.value
      FROM_EMAIL      = data.aws_ssm_parameter.from_email.value
      ROSTER_WEBSITE  = data.aws_ssm_parameter.roster_website.value
      ROSTER_USERNAME = data.aws_ssm_parameter.roster_username.value
      ROSTER_PASSWORD = data.aws_ssm_parameter.roster_password.value
    }
  }
}
