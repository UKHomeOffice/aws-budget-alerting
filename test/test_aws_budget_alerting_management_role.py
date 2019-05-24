from aws_budget_alerting_management_role import AlertingCreationRoleTemplate

EXPECTED_ALERTING_TEMPLATE = '''AWSTemplateFormatVersion: '2010-09-09'
Description: Template creating IAM resources (role) allowing to create cost alerting
  resources
Parameters:
  AssumeRoleName:
    Description: Name of the role that should be allowed to assume the role allowing
      to create the alerting resources
    Type: String
  LambdaBucketName:
    Description: Name of the S3 bucket name containing the package for the Lambda
      publishing a message to Slack
    Type: String
  RoleName:
    Default: AwsBudgetAlertingManagementRole
    Description: Name of the role to assume in order to have the access rights to
      manage cost alerting resources
    Type: String
Resources:
  AwsBudgetAlertingManagementPolicy:
    Properties:
      Description: Policy allowing managing alerting resources for AWS Budgets
      ManagedPolicyName: budget-alerting-management
      PolicyDocument:
        Statement:
          - Action:
              - cloudformation:*
            Effect: Allow
            Resource:
              - '*'
            Sid: AllowCloudFormationAdmin
          - Action:
              - lambda:*
            Effect: Allow
            Resource:
              - '*'
            Sid: AllowLambdaAdmin
          - Action:
              - sns:*
            Effect: Allow
            Resource:
              - '*'
            Sid: AllowSnsAdmin
          - Action:
              - budgets:*
            Effect: Allow
            Resource:
              - '*'
            Sid: AllowBudgetsAdmin
          - Action:
              - iam:AttachRolePolicy
              - iam:CreateRole
              - iam:CreateServiceLinkedRole
              - iam:DeleteRole
              - iam:DeleteRolePolicy
              - iam:DeleteServiceLinkedRole
              - iam:DetachRolePolicy
              - iam:GetRole
              - iam:GetRolePolicy
              - iam:GetServiceLinkedRoleDeletionStatus
              - iam:ListRole*
              - iam:PassRole
              - iam:PutRolePolicy
              - iam:SimulatePrincipalPolicy
              - iam:TagRole
              - iam:UntagRole
              - iam:UpdateAssumeRolePolicy
            Effect: Allow
            Resource:
              - '*'
            Sid: AllowIamRoleManagement
          - Action:
              - s3:*
            Effect: Allow
            Resource:
              - !Join
                - ''
                - - 'arn:aws:s3:::'
                  - !Ref 'LambdaBucketName'
              - !Join
                - ''
                - - 'arn:aws:s3:::'
                  - !Ref 'LambdaBucketName'
                  - /*
            Sid: AllowLambdaBucketReadWrite
        Version: '2012-10-17'
    Type: AWS::IAM::ManagedPolicy
  AwsBudgetAlertingManagementRole:
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Action:
              - sts:AssumeRole
            Effect: Allow
            Principal:
              AWS: !Join
                - ''
                - - 'arn:aws:iam::'
                  - !Ref 'AWS::AccountId'
                  - :role/
                  - !Ref 'AssumeRoleName'
      ManagedPolicyArns:
        - !Ref 'AwsBudgetAlertingManagementPolicy'
      RoleName: budget-alerting-management
    Type: AWS::IAM::Role
'''


def test_alerting_cf_template():
    assert EXPECTED_ALERTING_TEMPLATE == AlertingCreationRoleTemplate().to_yaml()
