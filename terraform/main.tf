# A CloudWatch pipeline that parses a JSON envelope, runs Grok on the line inside it,
# and routes each event to a log group with its own retention.

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# The pipeline finds this log group through its data source tags, which match
# data_source_name and data_source_type in pipeline/pipeline.yaml.
resource "aws_cloudwatch_log_group" "source" {
  name              = "/sample/checkout/source"
  retention_in_days = 1
  tags = {
    "cw:datasource:name" = "checkout"
    "cw:datasource:type" = "default"
  }
}

resource "aws_cloudwatch_log_group" "destination" {
  for_each = {
    audit  = 365
    errors = 30
    debug  = 7
  }
  name              = "/sample/checkout/${each.key}"
  retention_in_days = each.value
}

resource "aws_iam_role" "pipeline" {
  name_prefix = "sample-log-routing-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "pipeline" {
  name = "process-and-route"
  role = aws_iam_role.pipeline.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Only for this data source, so the role can't process other log groups.
      {
        Effect = "Allow"
        Action = "logs:ProcessWithPipeline"
        Resource = [
          "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/sample/checkout/source",
          "${aws_cloudwatch_log_group.source.arn}:*",
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceAccount"   = data.aws_caller_identity.current.account_id
            "logs:data_source_name" = "checkout"
            "logs:data_source_type" = "default"
          }
        }
      },
      # Routed destinations are authorized by this role, not by a log group resource policy.
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = [for group in aws_cloudwatch_log_group.destination : "${group.arn}:*"]
      },
    ]
  })
}

resource "aws_observabilityadmin_telemetry_pipeline" "this" {
  name = "sample-checkout-routing"

  configuration {
    body = replace(file("${path.module}/../pipeline/pipeline.yaml"), "SOURCE_ROLE_ARN", aws_iam_role.pipeline.arn)
  }

  depends_on = [aws_iam_role_policy.pipeline, aws_cloudwatch_log_group.source, aws_cloudwatch_log_group.destination]
}
