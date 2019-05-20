from aws_budget_alerting_management_role import AlertingCreationRoleTemplate

expected_alerting_template = '''AWSTemplateFormatVersion: '2010-09-09'
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
        - arn:aws:iam::aws:policy/AmazonSNSFullAccess
      Policies:
        - PolicyDocument:
            Statement:
              - Action:
                  - cloudformation:*
                Effect: Allow
                Resource:
                  - '*'
            Version: '2012-10-17'
          PolicyName: CloudFormationManagement
        - PolicyDocument:
            Statement:
              - Action:
                  - lambda:*
                Effect: Allow
                Resource:
                  - '*'
            Version: '2012-10-17'
          PolicyName: LambdaAccess
        - PolicyDocument:
            Statement:
              - Action:
                  - budgets:*
                Effect: Allow
                Resource:
                  - '*'
            Version: '2012-10-17'
          PolicyName: BudgetsAccess
        - PolicyDocument:
            Statement:
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
            Version: '2012-10-17'
          PolicyName: IamRoleManagement
        - PolicyDocument:
            Statement:
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
            Version: '2012-10-17'
          PolicyName: LambdaBucketAccess
      RoleName: budget-alerting-management-role
    Type: AWS::IAM::Role
'''


def test_alerting_cf_template():
    assert expected_alerting_template == AlertingCreationRoleTemplate().to_yaml()
