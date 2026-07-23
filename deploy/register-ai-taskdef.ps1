$ErrorActionPreference = "Stop"

$Region = "ap-northeast-2"
$AccountId = "086561632397"
$Family = "tuktak-ai-service-task"
$ContainerName = "ai-service"
$Image = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/tuktak-ai-service:latest"
$ExecutionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
$TaskRoleArn = "arn:aws:iam::${AccountId}:role/tuktak-ai-service-task-role"

$envMap = @{}
if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*#" -or $_ -notmatch "=") {
      return
    }
    $parts = $_ -split "=", 2
    $envMap[$parts[0].Trim()] = $parts[1].Trim()
  }
}

$envList = @(
  @{ name = "APP_NAME"; value = "TukTak AI Service" },
  @{ name = "APP_ENV"; value = "prod" },
  @{ name = "APP_HOST"; value = "0.0.0.0" },
  @{ name = "APP_PORT"; value = "8001" },
  @{ name = "DEBUG"; value = "false" },
  @{ name = "MAIN_BACKEND_URL"; value = "http://tuktak-main-backend-task-service.tuktak.local:8081" },
  @{ name = "CHROMA_PATH"; value = "./data/chroma" },
  @{ name = "CHROMA_REPAIR_CASE_COLLECTION"; value = "repair_cases" },
  @{ name = "CHROMA_RISK_DOCUMENT_COLLECTION"; value = "risk_documents_ko_sroberta_v2" },
  @{ name = "CHROMA_REPAIR_MANUAL_COLLECTION"; value = "repair_manuals" },
  @{ name = "CHROMA_PRICE_REFERENCE_COLLECTION"; value = "price_references" },
  @{ name = "PRICE_REFERENCE_FILE_PATH"; value = "data/price_reference/base_price_table.csv" },
  @{ name = "EMBEDDING_MODEL_NAME"; value = "BAAI/bge-m3" },
  @{ name = "IMAGE_EMBEDDING_MODEL_NAME"; value = "nomic-ai/nomic-embed-vision-v1.5" },
  @{ name = "AI_TORCH_DEVICE"; value = "cuda" },
  @{ name = "NLP_STRUCTURING_MODEL_NAME"; value = "KLUE-RoBERTa-base" },
  @{ name = "NLP_STRUCTURING_BASE_MODEL_NAME"; value = "klue/roberta-base" },
  @{ name = "NLP_STRUCTURING_MODEL_PATH"; value = "/opt/models/KLUE-RoBERTa-base" },
  @{ name = "NLP_STRUCTURING_AUTO_DOWNLOAD"; value = "true" },
  @{ name = "NLP_STRUCTURING_MAX_LENGTH"; value = "192" },
  @{ name = "NLP_STRUCTURING_MISSING_THRESHOLD"; value = "0.5" },
  @{ name = "OPENAI_ESTIMATE_MODEL"; value = "gpt-5-mini" },
  @{ name = "OPENAI_ESTIMATE_TIMEOUT_SECONDS"; value = "60" },
  @{ name = "OPENAI_RISK_REPORT_MODEL"; value = "gpt-5-mini" },
  @{ name = "OPENAI_RISK_REPORT_TIMEOUT_SECONDS"; value = "60" },
  @{ name = "RISK_EMBEDDING_MODEL_NAME"; value = "jhgan/ko-sroberta-multitask" },
  @{ name = "RISK_RAG_METADATA_PATH"; value = "data/rag_documents/rag_metadata_unified.xlsx" },
  @{ name = "RISK_RAG_TOP_K"; value = "3" },
  @{ name = "RISK_RAG_PRICE_THRESHOLD"; value = "0.30" },
  @{ name = "RISK_RAG_EXTRA_COST_THRESHOLD"; value = "0.55" },
  @{ name = "RISK_RAG_SAFETY_THRESHOLD"; value = "0.60" },
  @{ name = "RISK_RAG_CONTRACT_THRESHOLD"; value = "0.60" },
  @{ name = "RISK_RAG_FIELD_THRESHOLD"; value = "0.65" },
  @{ name = "AWS_REGION"; value = $Region },
  @{ name = "WARMUP_ON_STARTUP"; value = "true" },
  @{ name = "WARMUP_RISK_EMBEDDING"; value = "true" }
)

foreach ($key in @("NLP_STRUCTURING_HF_REPO_ID", "NLP_STRUCTURING_HF_REVISION", "S3_BUCKET_NAME")) {
  if ($envMap.ContainsKey($key) -and $envMap[$key]) {
    $envList += @{ name = $key; value = $envMap[$key] }
  }
}

if (-not ($envList | Where-Object { $_.name -eq "S3_BUCKET_NAME" })) {
  $envList += @{ name = "S3_BUCKET_NAME"; value = "tuktak-ai-estimate-images-086561632397-apne2" }
}

$taskDef = @{
  family = $Family
  networkMode = "awsvpc"
  requiresCompatibilities = @("EC2")
  taskRoleArn = $TaskRoleArn
  executionRoleArn = $ExecutionRoleArn
  cpu = "3500"
  memory = "14000"
  containerDefinitions = @(
    @{
      name = $ContainerName
      image = $Image
      essential = $true
      cpu = 3500
      memoryReservation = 12000
      portMappings = @(
        @{ containerPort = 8001; hostPort = 8001; protocol = "tcp" }
      )
      resourceRequirements = @(
        @{ type = "GPU"; value = "1" }
      )
      environment = $envList
      secrets = @(
        @{ name = "NLP_STRUCTURING_HF_TOKEN"; valueFrom = "arn:aws:ssm:${Region}:${AccountId}:parameter/tuktak/ai-service/NLP_STRUCTURING_HF_TOKEN" },
        @{ name = "OPENAI_API_KEY_AI_ESTIMATE"; valueFrom = "arn:aws:ssm:${Region}:${AccountId}:parameter/tuktak/ai-service/OPENAI_API_KEY_AI_ESTIMATE" },
        @{ name = "OPENAI_API_KEY_AI_RISKREPORT"; valueFrom = "arn:aws:ssm:${Region}:${AccountId}:parameter/tuktak/ai-service/OPENAI_API_KEY_AI_RISKREPORT" }
      )
      logConfiguration = @{
        logDriver = "awslogs"
        options = @{
          "awslogs-group" = "/ecs/tuktak-ai-service"
          "awslogs-region" = $Region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      healthCheck = @{
        command = @("CMD-SHELL", "curl -f http://localhost:8001/health || exit 1")
        interval = 30
        timeout = 10
        retries = 5
        startPeriod = 300
      }
    }
  )
}

$tmp = Join-Path $env:TEMP "tuktak-ai-taskdef.json"
$taskDef | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $tmp -Encoding ASCII
try {
  aws ecs register-task-definition `
    --region $Region `
    --cli-input-json "file://$tmp" `
    --query "taskDefinition.{Family:family,Revision:revision,TaskDefinitionArn:taskDefinitionArn}" `
    --output json
}
finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
