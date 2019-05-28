"""Script creating a CloudFormation template containing the resources required to set up budget
alerting to a Slack channel
"""

import sys
import os
from troposphere import Template, Parameter, Ref
from troposphere import sns, serverless, budgets, awslambda

LAMBDA_RUNTIME = 'nodejs8.10'


class AlertingTemplate(Template):
    """Class generating the CloudFormation template for AWS Budget alerting.

    To generate the template, create a new object of this class and call to_yaml() on it.
    """

    def add_topic_and_lambda(self, topic_name, function_description, function_name, webhook_url,
                             message_prefix):
        """Adds a SNS topic and SAM Function to the CloudFormation template

        :param topic_name: (str) the SNS topic name
        :param function_description: (str) the description for the SAM Serverless function
        :param function_name: (str) the name for the SAM Serverless function
        :param webhook_url: (str) the webhook URL for the Slack channel the message should be
                posted to

        :return: a sns.Topic object
        """
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
                    'MESSAGE_PREFIX': message_prefix,
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
        """Adds a topic policy to a topic object that allows it to be notified by the AWS Budgets
        service.

        :param topic: a sns.Topic object
        :return: the sns.TopicPolicy object
        """
        return self.add_resource(sns.TopicPolicy(
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
    """Gets a budgets.NotificationWithSubscribers object that can be used in the creation of a
    budgets.Budget object.

    :param notification_type: the notification type (shold be 'ACTUAL' or 'FORECASTED')
    :param threshold_param: the threshold parameter (a percentage)
    :param budget_topic: the sns.Topic object that should be notified
    :return:
    """
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
    """Generates a CloudFormation template with budget alerting resources

    :return: the CloudFormation template as a :obj:`str`
    """
    template = AlertingTemplate()
    template.set_description('Stack alerting forecasted and actual AWS budget overspend to Slack')
    template.set_version('2010-09-09')
    template.set_transform('AWS::Serverless-2016-10-31')

    # budget parameter
    monthly_budget_param = template.add_parameter(Parameter(
        'MonthlyBudget',
        Description='Monthly budget for the account (in USD)',
        Type='Number',
    ))

    # message prefix parameter
    message_prefix_param = template.add_parameter(Parameter(
        'MessagePrefix',
        Description='A string that will be pre-pend to alert messages, e.g. to specify a friendly'
                    ' AWS account name',
        Type='String',
        Default='',
    ))

    # params and resources linked to actual costs alerts
    actual_webhook_url_param = template.add_parameter(Parameter(
        'ActualCostWebHookUrl',
        Description='webhook for posting messages to the actual AWS cost Slack channel',
        Type='String',
    ))

    actual_budget_topic = \
        template.add_topic_and_lambda(topic_name='ActualBudgetAlert',
                                      function_description='Posts a message to the actual budget '
                                                           'alert Slack channel',
                                      function_name='ActualCostSlackNotification',
                                      webhook_url=Ref(actual_webhook_url_param),
                                      message_prefix=Ref(message_prefix_param))

    actual_threshold_param = template.add_parameter(Parameter(
        'ActualThreshold',
        Description='Threshold (percentage) compared to the actual cost that should trigger an '
                    'alert',
        Type='Number',
    ))

    actual_budget_subscriber = get_notification_with_subscriber('ACTUAL', actual_threshold_param,
                                                                actual_budget_topic)

    # params and resources linked to forecasted costs alerts
    forecasted_webhook_url_param = template.add_parameter(Parameter(
        'ForecastedCostWebHookUrl',
        Description='webhook for posting messages to the forecasted AWS cost Slack channel',
        Type='String',
    ))

    forecasted_budget_topic = \
        template.add_topic_and_lambda(topic_name='ForecastedBudgetAlert',
                                      function_description='Posts a message to the forecasted '
                                                           'budget alert Slack channel',
                                      function_name='ForecastedCostSlackNotification',
                                      webhook_url=Ref(forecasted_webhook_url_param),
                                      message_prefix=Ref(message_prefix_param))

    forecasted_threshold_param = template.add_parameter(Parameter(
        'ForecastedThreshold',
        Description='Threshold (percentage) compared to the forecasted cost that should trigger '
                    'an alert',
        Type='Number',
    ))
    forecasted_budget_subscriber = get_notification_with_subscriber('FORECASTED',
                                                                    forecasted_threshold_param,
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
    template.add_resource(budget)

    # Allow the AWS Budgets service to publish messages to our topics

    # actual costs alert topic
    template.add_topic_policy(actual_budget_topic)

    # forecasted costs alert topic
    template.add_topic_policy(forecasted_budget_topic)

    return template.to_yaml()


def main():
    """Main entry point
    """
    if len(sys.argv) != 1:
        print("usage: {}".format(os.path.basename(__file__)))
        print('prints a CloudFormation template')
        sys.exit(1)
    print(get_alerting_cf_template())


if __name__ == "__main__":
    main()
