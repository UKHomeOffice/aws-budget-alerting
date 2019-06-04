"""Script generating a CloudFormation template to create an S3 bucket accessible from the AWS
Lambda service
"""

from troposphere import Template, Parameter, Ref, Join
from troposphere import s3


def get_cf_template():
    """Generates CloudFormation code for creating an S3 bucket accessible from the Lambda service,
    therefore allowing the service to download lambda function packages

    :return: a string containing the CloudFormation template
    """
    template = Template()
    template.set_description('Creates an S3 bucket that can be used when uploading lambda packages')

    bucket_name_param = template.add_parameter(Parameter(
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
    template.add_resource(lambda_bucket)

    template.add_resource(s3.BucketPolicy(
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

    return template.to_yaml()


def main():
    """
    Main function entry point
    """
    print(get_cf_template())


if __name__ == "__main__":
    main()
