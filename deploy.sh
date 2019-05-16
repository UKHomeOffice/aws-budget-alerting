#!/usr/bin/env bash

function usage {
    cat << EOF
Usage: ${0} MONTHLY_BUDGET ACTUAL_THRESHOLD_PERCENTAGE FORECASTED_THRESHOLD_PERCENTAGE
Deploys a CloudFormation stack with AWS Budgets, SNS and Lambda resources that post a message to a slack channel.
MONTHLY_BUDGET is the monthly budget for all AWS costs for the account
ACTUAL_THRESHOLD_PERCENTAGE is the percentage of the budget that should trigger alerts for actual costs
FORECASTED_THRESHOLD_PERCENTAGE is the percentage of the budget that should trigger alerts for forecasted costs

On top of the parameters above, the following environment variables need to be set:
ACTUAL_COST_WEBHOOK_URL the URL for the actual cost alert channel
FORECASTED_COST_WEBHOOK_URL the URL for the forecasted cost alert channel
LAMBDA_PACKAGE_BUCKET the name of the S3 bucket to which the lambda function code has been uploaded
EOF
}

if [[ $# -ne 3 ]]; then
  usage
  exit 1
fi

MONTHLY_BUDGET=$1
ACTUAL_THRESHOLD_PERCENTAGE=$2
FORECASTED_THRESHOLD_PERCENTAGE=$3

if [[ -z "${ACTUAL_COST_WEBHOOK_URL+x}" ]]; then
    echo Environment variable ACTUAL_COST_WEBHOOK_URL should be defined
    exit 2
fi

if [[ -z "${FORECASTED_COST_WEBHOOK_URL+x}" ]]; then
    echo Environment variable FORECASTED_COST_WEBHOOK_URL should be defined
    exit 3
fi

set -euo pipefail

sam deploy \
  --template-file packaged.yaml \
  --stack-name budget-alerts \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides "MonthlyBudget=${MONTHLY_BUDGET}" \
  "ActualCostWebHookUrl=${ACTUAL_COST_WEBHOOK_URL}" \
  "ActualThreshold=${ACTUAL_THRESHOLD_PERCENTAGE}" \
  "ForecastedCostWebHookUrl=${FORECASTED_COST_WEBHOOK_URL}" \
  "ForecastedThreshold=${FORECASTED_THRESHOLD_PERCENTAGE}"
