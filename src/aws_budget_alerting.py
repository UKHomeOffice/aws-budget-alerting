import sys
import os
from troposphere import Template, Parameter, Ref, GetAtt
from troposphere import sns, serverless, budgets, awslambda

LAMBDA_RUNTIME = 'nodejs8.10'


class AlertingTemplate(Template):

    def add_topic_and_lambda(self, topic_name, function_description, function_name, webhook_url):
        topic = sns.Topic(
            "{}Topic".format(topic_name),
            TopicName=topic_name,
        )
        self.add_resource(topic)

        self.add_resource(serverless.Function(
            "{}Lambda".format(function_name),
            Description=function_description,
            MemorySize=128,
            FunctionName=function_name,
            Runtime=LAMBDA_RUNTIME,
            Handler='index.handler',
            CodeUri='lambda-src/',
            Timeout=10,
            Environment=awslambda.Environment(
                Variables={
                    'WEBHOOK_URL': webhook_url,
                }),
            Events={
                'SNS': serverless.SNSEvent(
                    'sns',
                    Topic=Ref(topic)
                ),
            },
        ))
        return topic

    def add_topic_policy(self, topic):
        self.add_resource(sns.TopicPolicy(
            "{}Policy".format(topic.title),
            PolicyDocument={
                "Id": "BudgetTopicPolicy",
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "AWSBudgets-sns-notification",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "budgets.amazonaws.com"
                    },
                    "Action": "SNS:Publish",
                    "Resource": Ref(topic),
                }],
            },
            Topics=[Ref(topic)],
        ))


def get_notification_with_subscriber(notification_type, threshold_param, budget_topic):
    # notification_type should be 'ACTUAL' 'FORECASTED'
    return budgets.NotificationWithSubscribers(
        Notification=budgets.Notification(
            ComparisonOperator='GREATER_THAN',
            NotificationType=notification_type,
            Threshold=Ref(threshold_param),
            ThresholdType='PERCENTAGE',
        ),
        Subscribers=[budgets.Subscriber(
            Address=Ref(budget_topic),
            SubscriptionType='SNS',
        )],
    )


def get_alerting_cf_template():
    t = AlertingTemplate()
    t.set_description('Stack alerting forecasted and actual AWS budget overspend to Slack')
    t.set_version('2010-09-09')
    t.set_transform('AWS::Serverless-2016-10-31')

    # budget parameter
    monthly_budget_param = t.add_parameter(Parameter(
        'MonthlyBudget',
        Description='Monthly budget for the account (in USD)',
        Type='Number',
    ))

    # params and resources linked to actual costs alerts
    actual_webhook_url_param = t.add_parameter(Parameter(
        'ActualCostWebHookUrl',
        Description='webhook for posting messages to the actual AWS cost Slack channel',
        Type='String',
    ))

    actual_budget_topic = t.add_topic_and_lambda(topic_name='ActualBudgetAlert',
                                                 function_description='Posts a message to the actual budget alert Slack channel',
                                                 function_name='ActualCostSlackNotification',
                                                 webhook_url=Ref(actual_webhook_url_param))

    actual_threshold_param = t.add_parameter(Parameter(
        'ActualThreshold',
        Description='Threshold (percentage) compared to the actual cost that should trigger an alert',
        Type='Number',
    ))

    actual_budget_subscriber = get_notification_with_subscriber('ACTUAL', actual_threshold_param, actual_budget_topic)

    # params and resources linked to forecasted costs alerts
    forecasted_webhook_url_param = t.add_parameter(Parameter(
        'ForecastedCostWebHookUrl',
        Description='webhook for posting messages to the forecasted AWS cost Slack channel',
        Type='String',
    ))

    forecasted_budget_topic = t.add_topic_and_lambda(topic_name='ForecastedBudgetAlert',
                                                     function_description='Posts a message to the forecasted budget alert Slack channel',
                                                     function_name='ForecastedCostSlackNotification',
                                                     webhook_url=Ref(forecasted_webhook_url_param))

    forecasted_threshold_param = t.add_parameter(Parameter(
        'ForecastedThreshold',
        Description='Threshold (percentage) compared to the forecasted cost that should trigger an alert',
        Type='Number',
    ))
    forecasted_budget_subscriber = get_notification_with_subscriber('FORECASTED', forecasted_threshold_param,
                                                                    forecasted_budget_topic)

    # AWS Budgets budget resource
    budget = budgets.Budget(
        'Budget',
        Budget=budgets.BudgetData(
            BudgetType='COST',
            TimeUnit='MONTHLY',
            BudgetName='Monthly Budget',
            BudgetLimit=budgets.Spend(
                Amount=Ref(monthly_budget_param),
                Unit='USD',
            ),
        ),
        NotificationsWithSubscribers=[
            actual_budget_subscriber,
            forecasted_budget_subscriber,
        ],
    )
    t.add_resource(budget)

    # Allow the AWS Budgets service to publish messages to our topics

    # actual costs alert topic
    t.add_topic_policy(actual_budget_topic)

    # forecasted costs alert topic
    t.add_topic_policy(forecasted_budget_topic)

    return t.to_yaml()


def main():
    if len(sys.argv) != 1:
        print("usage: {}".format(os.path.basename(__file__)))
        print('prints a CloudFormation template')
        sys.exit(1)
    print(get_alerting_cf_template())


if __name__ == "__main__":
    main()
