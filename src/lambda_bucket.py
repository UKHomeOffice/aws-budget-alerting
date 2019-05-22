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

    lambda_bucket = s3.Bucket(
        'LambdaBucket',
        BucketName=Ref(bucket_name_param),
        BucketEncryption=s3.BucketEncryption(
            ServerSideEncryptionConfiguration=[
                s3.ServerSideEncryptionRule(
                    ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                        SSEAlgorithm='AES256',  # alternative is 'aws:kms'
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
    print(get_cf_template())


if __name__ == "__main__":
    main()
