resource "aws_iam_role" "lambda_bronze" {
  name = "lambda-bronze-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_bronze.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_bronze.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-bronze-s3-policy"
  role = aws_iam_role.lambda_bronze.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}
resource "aws_iam_role" "lambda_silver" {
  name = "lambda-silver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_silver_basic" {
  role       = aws_iam_role.lambda_silver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_silver_vpc" {
  role       = aws_iam_role.lambda_silver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_silver_s3" {
  name = "lambda-silver-s3-policy"
  role = aws_iam_role.lambda_silver.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = "${var.s3_bucket_arn}/bronze/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = "${var.s3_bucket_arn}/silver/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
        ]
        Resource = var.s3_bucket_arn
      }
    ]
  })
}
resource "aws_iam_role" "discord_notifier_role" {
  name = "discord-notifier-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}
resource "aws_iam_role_policy_attachment" "discord_notifier_basic" {
  role       = aws_iam_role.discord_notifier_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role" "lambda_gold" {
  name = "lambda-gold-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "lambda_gold_basic" {
  role       = aws_iam_role.lambda_gold.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


resource "aws_iam_role_policy_attachment" "lambda_gold_vpc" {
  role       = aws_iam_role.lambda_gold.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}


resource "aws_iam_role_policy" "lambda_gold_s3" {
  name = "lambda-gold-s3-policy"
  role = aws_iam_role.lambda_gold.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.s3_bucket_arn}/silver/*"
      },

      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/gold/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = var.s3_bucket_arn
      }
    ]
  })
}