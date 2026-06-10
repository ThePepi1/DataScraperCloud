data "archive_file" "bronze_layer" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = var.lambda_output_path
}

resource "aws_lambda_function" "bronze_layer" {
  filename         = data.archive_file.bronze_layer.output_path
  function_name    = "bronze_layer_lambda"
  handler          = "handler.handler"
  runtime          = "python3.12"
  role             = var.lambda_role_arn
  timeout          = 300
  memory_size      = 256
  source_code_hash = data.archive_file.bronze_layer.output_base64sha256

  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}
