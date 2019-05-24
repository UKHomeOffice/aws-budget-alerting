"""Script generating a CloudFormation stack creating a role that when assumed will allow the
resources required for AWS Budget alerting to be created.
"""
import sys
import os
from troposphere import Template, Parameter, Ref, Join
from troposphere import iam


class AlertingCreationRoleTemplate(Template):
    """Template class dealing with the generation of the CloudFormation template containing a role
    that allows managing the resources required for AWS Budget alerting
    """

    def __init__(self):
        """Constructor for the AlertingCreationRoleTemplate class.

        Call to_yaml() on an object of this class to get a string containing the CloudFormation
        template
        """
        Template.__init__(self)
        self.set_description('Template creating IAM resources (role) allowing to create cost '
                             'alerting resources')
        self.set_version('2010-09-09')

        # parameters
        self.assume_role_name_param = self.add_parameter(Parameter(
            'AssumeRoleName',
            Description='Name of the role that should be allowed to assume the role allowing to '
                        'create the alerting resources',
            Type='String',
        ))
        self.role_name_param = self.add_parameter(Parameter(
            'RoleName',
            Description='Name of the role to assume in order to have the access rights to manage '
                        'cost alerting resources',
            Type='String',
            Default='AwsBudgetAlertingManagementRole',
        ))
        self.lambda_bucket_name_param = self.add_parameter(Parameter(
            'LambdaBucketName',
            Description='Name of the S3 bucket name containing the package for the Lambda '
                        'publishing a message to Slack',
            Type='String',
        ))

        managed_policy = self._create_policy()
        self._create_role(managed_policy)

    def _create_policy(self):
        """
        Creates a managed policy (iam.Policy) with the permissions required to manage AWS Budget
        alerting resources.

        :return: an iam.ManagedPolicy object
        """
        return self.add_resource(iam.ManagedPolicy(
            'AwsBudgetAlertingManagementPolicy',
            Description='Policy allowing managing alerting resources for AWS Budgets',
            ManagedPolicyName='budget-alerting-management',
            PolicyDocument={"Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "AllowCloudFormationAdmin",
                                    "Action": [
                                        "cloudformation:*",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": ["*"]
                                },
                                {
                                    "Sid": "AllowLambdaAdmin",
                                    "Action": [
                                        "lambda:*",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": ["*"]
                                },
                                {
                                    "Sid": "AllowSnsAdmin",
                                    "Action": [
                                        "sns:*",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": ["*"]
                                },
                                {
                                    "Sid": "AllowBudgetsAdmin",
                                    "Action": [
                                        "budgets:*",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": ["*"]
                                },
                                {
                                    "Sid": "AllowIamRoleManagement",
                                    "Action": [
                                        "iam:AttachRolePolicy",
                                        "iam:CreateRole",
                                        "iam:CreateServiceLinkedRole",
                                        "iam:DeleteRole",
                                        "iam:DeleteRolePolicy",
                                        "iam:DeleteServiceLinkedRole",
                                        "iam:DetachRolePolicy",
                                        "iam:GetRole",
                                        "iam:GetRolePolicy",
                                        "iam:GetServiceLinkedRoleDeletionStatus",
                                        "iam:ListRole*",
                                        "iam:PassRole",
                                        "iam:PutRolePolicy",
                                        "iam:SimulatePrincipalPolicy",
                                        "iam:TagRole",
                                        "iam:UntagRole",
                                        "iam:UpdateAssumeRolePolicy",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": ["*"]
                                },
                                {
                                    "Sid": "AllowLambdaBucketReadWrite",
                                    "Action": [
                                        "s3:*",
                                    ],
                                    "Effect": "Allow",
                                    "Resource": [
                                        Join('', [
                                            'arn:aws:s3:::',
                                            Ref(self.lambda_bucket_name_param),
                                        ]),
                                        Join('', [
                                            'arn:aws:s3:::',
                                            Ref(self.lambda_bucket_name_param),
                                            '/*',
                                        ]),
                                    ]
                                },
                            ]
                            },
        ))

    def _create_role(self, managed_policy):
        """
        Adds a iam.Role to the template.

        The role will have sufficient privileges to manage the resources required for alerts
        related to AWS Budgets

        :param managed_policy: the managed policy to associate with this role (iam.ManagedPolicy)

        :return: an iam.Role object
        """
        return self.add_resource(iam.Role(
            'AwsBudgetAlertingManagementRole',
            RoleName='budget-alerting-management',
            AssumeRolePolicyDocument={
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        # arn:aws:iam::AWS-account-ID:role/role-name
                        "AWS": Join('', [
                            'arn:aws:iam::',
                            Ref("AWS::AccountId"),
                            ':role/',
                            Ref(self.assume_role_name_param)
                        ])
                    },
                    "Action": ["sts:AssumeRole"]
                }]
            },
            ManagedPolicyArns=[
                Ref(managed_policy)
            ],
        ))


def main():
    """Main entry point
    """
    if len(sys.argv) != 1:
        print("usage: {}".format(os.path.basename(__file__)))
        print(
            'prints a CloudFormation template container IAM resources to create AWS cost alerting '
            'resources')
        sys.exit(1)
    print(AlertingCreationRoleTemplate().to_yaml())


if __name__ == "__main__":
    main()
