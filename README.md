# Setting up alerts for AWS Budgets

This repo contains cloudformation templates that can be used to create a stack monitoring AWS Budgets and posting messages to a Slack channel if the actual or the forecasted costs  are above given thresholds.

The CloudFormation stacks are created using Troposphere.

The overall architecture of the solution is as follows:

AWS Budgets budget -> AWS Budgets trigger -> SNS topics -> AWS lambdas -> Slack channels

The solution supports different Slack channels for actual and forecasted events, in an attempt to avoid notification fatigue.

## Set up credentials

Set up credentials allowing to create Budgets, SNS topics, Lambdas

For example, the following will start a prompt with temporary credentials for a profile name stored in environment variable `AWS_PROFILE_NAME`:

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

## TODO

* unit tests for nodejs handler
* apply to all environments

* test: waiting for threshold to be reached; DONE
* modify handler to deal with event.Records list; DONE
* configure alerts for forecasted amounts; DONE
* Makefile; DONE

* ecnryption of params (WEBHOOK_URL); on hold: ok as it is for Slack; will need something better for ServiceNow integration
