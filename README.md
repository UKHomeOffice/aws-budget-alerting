# Setting up alerts for AWS Budgets

This repo contains cloudformation templates that can be used to create a stack monitoring AWS Budgets and post messages to a Slack channel if the actual or the forecasted costs are above given thresholds.

The CloudFormation stacks are created using Troposphere.

The overall architecture of the solution is as follows:

AWS Budgets budget -> AWS Budgets trigger -> SNS topics -> AWS lambdas -> Slack channels

The solution supports different Slack channels for actual and forecasted events, in an attempt to avoid notification fatigue.

This repo contains the AWS resource definitions and the AWS Lambda required to put notifications in place.

To see an example of how it is used in a GitOps way to modify threshold for an account, please see the [aws-budget-alerting-config](https://github.com/UKHomeOffice/aws-budget-alerting-config) repo.
All the steps described below are taken care of in that repo's Drone pipeline.

## Set up credentials

Set up credentials allowing to create Budgets, SNS topics, Lambdas

For example, the following will start a prompt with temporary credentials for a profile name stored in environment variable `AWS_PROFILE_NAME` if you use aws-vault to securely store your AWS credentials:

```bash
# NOTE: set env variable AWS_PROFILE_NAME
aws-vault exec $AWS_PROFILE_NAME -assume-role-ttl=60m  --
```

Create a new python environment and install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Subsequently, activate a Python virtual environments
```bash
source venv/bin/activate
```

## Environment variables

The following environment variables need to be set in order to be able to package and deploy the alerting solution:

* `ACTUAL_COST_WEBHOOK_URL`: URL for the Slack channel the actual costs alerts need to be sent to
* `FORECAST_COST_WEBHOOK_URL`: URL for the Slack channel the forecasted costs alerts need to be sent to
* `LAMBDA_PACKAGE_BUCKET`: name of the bucket the lambda function should be uploaded to

## Setting up an S3 Bucket for lambda

If your AWS account doesn't currently have an S3 bucket the lambda package can be uploaded to, you can create one with:

```bash
aws cloudformation create-stack --stack-name lambda-bucket \
  --template-body "$(python src/lambda_bucket.py)" \
  --parameters ParameterKey=BucketName,ParameterValue=$LAMBDA_PACKAGE_BUCKET
```

## Setting up a role to allow you to manage the alerting resources

If your AWS account doesn't currently have a role that allows you to manage the alerting resources, you can create one by deploying the following stack:

The following command expects that you have defined an environment variable called ASSUME_ROLE_NAME that contains the name of a role that will be allowed to assume the alerting management role being created.

```bash
aws cloudformation create-stack --stack-name budget-alerting-management-role \
  --template-body "$(python src/aws_budget_alerting_management_role.py)" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=LambdaBucketName,ParameterValue=$LAMBDA_PACKAGE_BUCKET \
  ParameterKey=AssumeRoleName,ParameterValue=$ASSUME_ROLE_NAME
```

```bash
rm aws_budget_alerting_management_role.yaml || true
python src/aws_budget_alerting_management_role.py > aws_budget_alerting_management_role.yaml
aws cloudformation deploy \
  --template-file aws_budget_alerting_management_role.yaml \
  --stack-name budget-alerting-management-role \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides "LambdaBucketName=${LAMBDA_PACKAGE_BUCKET}" \
  "AssumeRoleName=${ASSUME_ROLE_NAME}"
```

## Package

The following will build and package the lambda function:

```bash
make
```

## Deploy

```bash
./deploy.sh MONTHLY_BUDGET ACTUAL_THRESHOLD_PERCENTAGE FORECAST_THRESHOLD_PERCENTAGE
```

e.g. 

```bash
./deploy.sh 1200 100 120
```

Will deploy an alerting mechanism that will trigger alerts when the actual cost is 100% of the $1,200 monthly budget and when the forecasted cost is 120% of the budget.

Because CloudFormation doesn't seem to be able to amend a budget, it is currently necessary to destroy the budget before deploying a change.

Therefore, deleting the existing stack is recommended:

```bash
make delete-stack
```

A full build and deployment would look like:

```bash
make && make delete-stack && ./deploy.sh MONTHLY_BUDGET ACTUAL_THRESHOLD_PERCENTAGE FORECAST_THRESHOLD_PERCENTAGE
```

## Parameter validation

The following script can be run to validate the parameters to be passed to `deploy.sh`.

```bash
python3 src/aws_budget_check_params.py MONTHLY_BUDGET ACTUAL_THRESHOLD_PERCENTAGE FORECAST_THRESHOLD_PERCENTAGE
```

The script returns 0 if the parameters passed will potentially trigger an alert.

If one of the threshold percentages is too low to be able to trigger an alert, a non-zero value is returned.

The validation that occurs is:

MONTHLY_BUDGET * ACTUAL_THRESHOLD_PERCENTAGE > AWS calculated actual cost

MONTHLY_BUDGET * FORECAST_THRESHOLD_PERCENTAGE > AWS calculated forecasted cost

