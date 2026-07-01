

resource "aws_cloudwatch_log_group" "pipeline_state_machine" {
  name              = "/aws/vendedlogs/states/data-pipeline"
  retention_in_days = 30
}


resource "aws_sfn_state_machine" "data_pipeline" {
  name     = "data-pipeline-state-machine"
  role_arn = var.step_function_role_arn

  definition = jsonencode({
    Comment = "Bronze -> Silver (HN normalize) -> Gold -> Sync pipeline"
    StartAt = "BronzeLayer"
    States = {

      BronzeLayer = {
        Type       = "Task"
        Resource   = var.bronze_lambda_arn
        Comment    = "Povlači podatke sa HN Algolia API-ja i piše u bronze/hackernews/"
        ResultPath = "$.bronze_result"
        Next       = "NormalizeHN"
      }

      NormalizeHN = {
        Type     = "Task"
        Resource = var.normalize_hn_lambda_arn
        Comment  = "Normalizuje bronze HN fajlove iz prethodnog koraka u silver tabele"

        InputPath  = "$.bronze_result"
        ResultPath = "$.normalize_result"
        Next       = "GoldLayer"
      }

      GoldLayer = {
        Type     = "Task"
        Resource = var.gold_lambda_arn
        Comment  = "Agregira silver tabele u gold sloj (top users, daily stats, itd.) za sve dane koje je normalize_hn obradio"

        Parameters = {
          "dates.$" = "$.normalize_result.dates"
        }
        ResultPath = "$.gold_result"
        Next       = "LambdaSync"
      }

      LambdaSync = {
        Type     = "Task"
        Resource = var.lambda_sync_lambda_arn
        Comment  = "Sinhronizuje gold parquet tabele u PostgreSQL za sve dane koje je gold obradio"
        InputPath  = "$.gold_result"
        ResultPath = "$.sync_result"
        End        = true
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.pipeline_state_machine.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }
}



resource "aws_iam_role" "eventbridge_start_pipeline" {
  name = "eventbridge-start-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_start_pipeline_policy" {
  name = "eventbridge-start-pipeline-policy"
  role = aws_iam_role.eventbridge_start_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = aws_sfn_state_machine.data_pipeline.arn
      }
    ]
  })
}



resource "aws_cloudwatch_event_rule" "pipeline_daily" {
  name                = "data-pipeline-daily"
  schedule_expression = var.schedule_expression
  description         = "Pokreće ceo bronze->silver->gold->sync lanac jednom dnevno"
}

resource "aws_cloudwatch_event_target" "pipeline_target" {
  rule      = aws_cloudwatch_event_rule.pipeline_daily.name
  target_id = "data_pipeline_state_machine"
  arn       = aws_sfn_state_machine.data_pipeline.arn
  role_arn  = aws_iam_role.eventbridge_start_pipeline.arn
}
