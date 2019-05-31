"""Test the CloudFormation template generated to manage the S3 bucket where the AWS Lambda code
is going to be uploaded to.
"""
from lambda_bucket import get_cf_template

# pylint: disable=line-too-long
EXPECTED_TEMPLATE = '''Description: Creates an S3 bucket that can be used when uploading lambda packages
Parameters:
  BucketName:
    Description: Name of the S3 bucket that will contain lambda packages
    Type: String
Resources:
  LambdaBucket:
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Ref 'BucketName'
      VersioningConfiguration:
        Status: Enabled
    Type: AWS::S3::Bucket
  LambdaBucketPolicy:
    Properties:
      Bucket: !Ref 'LambdaBucket'
      PolicyDocument:
        Statement:
          - Action:
              - s3:Get*
              - s3:List*
            Effect: Allow
            Principal:
              Service:
                - lambda.amazonaws.com
            Resource:
              - !Join
                - ''
                - - 'arn:aws:s3:::'
                  - !Ref 'BucketName'
              - !Join
                - ''
                - - 'arn:aws:s3:::'
                  - !Ref 'BucketName'
                  - /*
            Sid: ReadPerm
        Version: '2012-10-17'
    Type: AWS::S3::BucketPolicy
'''
# pylint: enable=line-too-long


def test_lambda_bucket_cf_template():
    """Test the CloudFormation template generated by Troposphere to create the bucket used to store
    the AWS Lambda code.

    :return: None
    """
    assert EXPECTED_TEMPLATE == get_cf_template()