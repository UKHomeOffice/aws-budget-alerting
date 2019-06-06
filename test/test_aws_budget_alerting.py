from aws_budget_alerting import get_alerting_cf_template

EXPECTED_ALERTING_TEMPLATE = '''AWSTemplateFormatVersion: '2010-09-09'
Description: Stack alerting forecasted and actual AWS budget overspend to Slack
Parameters:
  ActualCostWebHookUrl:
    Description: webhook for posting messages to the actual AWS cost Slack channel
    Type: String
  ActualThreshold:
    Description: Threshold (percentage) compared to the actual cost that should trigger
      an alert
    Type: Number
  ForecastedCostWebHookUrl:
    Description: webhook for posting messages to the forecasted AWS cost Slack channel
    Type: String
  ForecastedThreshold:
    Description: Threshold (percentage) compared to the forecasted cost that should
      trigger an alert
    Type: Number
  MessagePrefix:
    Default: ''
    Description: A string that will be pre-pend to alert messages, e.g. to specify
      a friendly AWS account name
    Type: String
  MonthlyBudget:
    Description: Monthly budget for the account (in USD)
    Type: Number
Resources:
  ActualBudgetAlertTopic:
    Properties:
      TopicName: ActualBudgetAlert
    Type: AWS::SNS::Topic
  ActualBudgetAlertTopicPolicy:
    Properties:
      PolicyDocument:
        Id: BudgetTopicPolicy
        Statement:
          - Action: SNS:Publish
            Effect: Allow
            Principal:
              Service: budgets.amazonaws.com
            Resource: !Ref 'ActualBudgetAlertTopic'
            Sid: AWSBudgets-sns-notification
        Version: '2012-10-17'
      Topics:
        - !Ref 'ActualBudgetAlertTopic'
    Type: AWS::SNS::TopicPolicy
  ActualCostSlackNotificationLambda:
    Properties:
      CodeUri: lambda-src/
      Description: Posts a message to the actual budget alert Slack channel
      Environment:
        Variables:
          MESSAGE_PREFIX: !Ref 'MessagePrefix'
          WEBHOOK_URL: !Ref 'ActualCostWebHookUrl'
      Events:
        SNS:
          Properties:
            Topic: !Ref 'ActualBudgetAlertTopic'
          Type: SNS
      FunctionName: ActualCostSlackNotification
      Handler: index.handler
      MemorySize: 128
      Runtime: nodejs8.10
      Timeout: 10
    Type: AWS::Serverless::Function
  Budget:
    Properties:
      Budget:
        BudgetLimit:
          Amount: !Ref 'MonthlyBudget'
          Unit: USD
        BudgetName: Monthly Budget
        BudgetType: COST
        TimeUnit: MONTHLY
      NotificationsWithSubscribers:
        - Notification:
            ComparisonOperator: GREATER_THAN
            NotificationType: ACTUAL
            Threshold: !Ref 'ActualThreshold'
            ThresholdType: PERCENTAGE
          Subscribers:
            - Address: !Ref 'ActualBudgetAlertTopic'
              SubscriptionType: SNS
        - Notification:
            ComparisonOperator: GREATER_THAN
            NotificationType: FORECASTED
            Threshold: !Ref 'ForecastedThreshold'
            ThresholdType: PERCENTAGE
          Subscribers:
            - Address: !Ref 'ForecastedBudgetAlertTopic'
              SubscriptionType: SNS
    Type: AWS::Budgets::Budget
  ForecastedBudgetAlertTopic:
    Properties:
      TopicName: ForecastedBudgetAlert
    Type: AWS::SNS::Topic
  ForecastedBudgetAlertTopicPolicy:
    Properties:
      PolicyDocument:
        Id: BudgetTopicPolicy
        Statement:
          - Action: SNS:Publish
            Effect: Allow
            Principal:
              Service: budgets.amazonaws.com
            Resource: !Ref 'ForecastedBudgetAlertTopic'
            Sid: AWSBudgets-sns-notification
        Version: '2012-10-17'
      Topics:
        - !Ref 'ForecastedBudgetAlertTopic'
    Type: AWS::SNS::TopicPolicy
  ForecastedCostSlackNotificationLambda:
    Properties:
      CodeUri: lambda-src/
      Description: Posts a message to the forecasted budget alert Slack channel
      Environment:
        Variables:
          MESSAGE_PREFIX: !Ref 'MessagePrefix'
          WEBHOOK_URL: !Ref 'ForecastedCostWebHookUrl'
      Events:
        SNS:
          Properties:
            Topic: !Ref 'ForecastedBudgetAlertTopic'
          Type: SNS
      FunctionName: ForecastedCostSlackNotification
      Handler: index.handler
      MemorySize: 128
      Runtime: nodejs8.10
      Timeout: 10
    Type: AWS::Serverless::Function
Transform: AWS::Serverless-2016-10-31
'''


def test_alerting_cf_template():
    assert EXPECTED_ALERTING_TEMPLATE == get_alerting_cf_template()
