data "archive_file" "bronze_layer" {
    type        = "zip"
    source_dir  = "../lambdas/bronze-layer"
    output_path = "../lambdas/bronze-layer.zip"
}


resource "aws_lambda_function" "bronze_layer" {
    filename      = data.archive_file.bronze_layer.output_path
    function_name = "bronze_layer_lambda"
    handler       = "handler.handler"
    runtime       = "python3.12"
    role          = aws_iam_role.lambda_bronze.arn
    timeout = 300
    memory_size = 256
    source_code_hash = data.archive_file.bronze_layer.output_base64sha256
}