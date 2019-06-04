from lambda_bucket import get_cf_template

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


def test_lambda_bucket_cf_template():
    assert EXPECTED_TEMPLATE == get_cf_template()
