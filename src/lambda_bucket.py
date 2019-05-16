import sys
import os
from troposphere import Template, Parameter, Ref, GetAtt, Join
from troposphere import s3, kms


def get_cf_template():
    t = Template()
    t.set_description('Creates an S3 bucket that can be used when uploading lambda packages')

    bucket_name_param = t.add_parameter(Parameter(
        'BucketName',
        Description='Name of the S3 bucket that will contain lambda packages',
        Type='String',
    ))

    # aws_account_ids_param = t.add_parameter(Parameter(
    #     'AwsAccountIds',
    #     Description='List of account ids from which the Lambda services will download the lambda packages from',
    #     Type='CommaDelimitedList',
    # ))

    # t.add_resource(kms.Key(
    #     'LambdaBucketKey',
    #
    # ))

    lambda_bucket = s3.Bucket(
        'LambdaBucket',
        BucketName=Ref(bucket_name_param),
        BucketEncryption=s3.BucketEncryption(
            ServerSideEncryptionConfiguration=[
                s3.ServerSideEncryptionRule(
                    ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                        # KMSMasterKeyID=,
                        # SSEAlgorithm='aws:kms',  # AES256
                        SSEAlgorithm='AES256',
                    )
                )
            ]
        ),
        VersioningConfiguration=s3.VersioningConfiguration(
            Status='Enabled',
        )
    )
    t.add_resource(lambda_bucket)

    t.add_resource(s3.BucketPolicy(
        'LambdaBucketPolicy',
        Bucket=Ref(lambda_bucket),
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "ReadPerm",
                "Effect": "Allow",
                "Principal":
                    {
                        "Service": [
                            "lambda.amazonaws.com",
                        ],
                    },
                "Action": [
                    "s3:Get*",
                    "s3:List*",
                ],
                "Resource": [
                    Join('', ['arn:aws:s3:::', Ref(bucket_name_param)]),
                    Join('', ['arn:aws:s3:::', Ref(bucket_name_param), '/*']),
                ],
            }]}

    ))

    return t.to_yaml()


def main():
    #     if len(sys.argv) < 3:
    #         print('''
    # usage: {} BUCKET_NAME [AWS_ACCOUNT_ID_1, AWS_ACCOUNT_ID_2, ...]
    # Creates an S3 bucket for lambda packages where:
    # BUCKET_NAME is the name of the bucket to create
    # AWS_ACCOUNT_ID_1, AWS_ACCOUNT_ID_2, ... are the ids of the AWS accounts in which the Lambda services should be allowed to read the bucket
    # '''.format(os.path.basename(__file__)))
    #         sys.exit(1)
    #
    #     bucket_name = sys.argv[1]
    #     aws_account_ids = sys.argv[2:len(sys.argv)]
    #     print_cf_template(bucket_name, aws_account_ids)
    print(get_cf_template())


if __name__ == "__main__":
    main()
