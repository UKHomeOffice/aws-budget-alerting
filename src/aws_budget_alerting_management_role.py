import sys
import os
from troposphere import Template, Parameter, Ref, GetAtt, Join
from troposphere import iam


class AlertingCreationRoleTemplate(Template):

    def __init__(self):
        Template.__init__(self)
        self.set_description('Template creating IAM resources (role) allowing to create cost alerting resources')
        self.set_version('2010-09-09')

        # parameters
        self.assume_role_name_param = self.add_parameter(Parameter(
            'AssumeRoleName',
            Description='Name of the role that should be allowed to assume the role allowing to create the alerting resources',
            Type='String',
        ))
        self.role_name_param = self.add_parameter(Parameter(
            'RoleName',
            Description='Name of the role to assume in order to have the access rights to manage cost alerting resources',
            Type='String',
            Default='AwsBudgetAlertingManagementRole',
        ))
        self.lambda_bucket_name_param = self.add_parameter(Parameter(
            'LambdaBucketName',
            Description='Name of the S3 bucket name containing the package for the Lambda publishing a message to Slack',
            Type='String',
        ))

        self.create_role()

    def create_role(self):
        self.add_resource(iam.Role(
            'AwsBudgetAlertingManagementRole',
            RoleName='budget-alerting-management-role',
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
                'arn:aws:iam::aws:policy/AmazonSNSFullAccess',
            ],
            Policies=[
                iam.Policy(
                    PolicyDocument={"Version": "2012-10-17",
                                    "Statement": [
                                        {
                                            "Action": [
                                                "cloudformation:*",
                                            ],
                                            "Effect": "Allow",
                                            "Resource": ["*"]
                                        },
                                    ]
                                    },
                    PolicyName='CloudFormationManagement',
                ),
                iam.Policy(
                    PolicyDocument={"Version": "2012-10-17",
                                    "Statement": [
                                        {
                                            "Action": [
                                                "lambda:*",
                                            ],
                                            "Effect": "Allow",
                                            "Resource": ["*"]
                                        },
                                    ]
                                    },
                    PolicyName='LambdaAccess',
                ),
                iam.Policy(
                    PolicyDocument={"Version": "2012-10-17",
                                    "Statement": [
                                        {
                                            "Action": [
                                                "budgets:*",
                                            ],
                                            "Effect": "Allow",
                                            "Resource": ["*"]
                                        },
                                    ]
                                    },
                    PolicyName='BudgetsAccess',
                ),
                iam.Policy(
                    PolicyDocument={"Version": "2012-10-17",
                                    "Statement": [
                                        {
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
                                    ]
                                    },
                    PolicyName='IamRoleManagement',
                ),
                iam.Policy(
                    PolicyDocument={"Version": "2012-10-17",
                                    "Statement": [
                                        {
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
                    PolicyName='LambdaBucketAccess',
                )],
        ))


def main():
    if len(sys.argv) != 1:
        print("usage: {}".format(os.path.basename(__file__)))
        print('prints a CloudFormation template container IAM resources to create AWS cost alerting resources')
        sys.exit(1)
    print(AlertingCreationRoleTemplate().to_yaml())


if __name__ == "__main__":
    main()
