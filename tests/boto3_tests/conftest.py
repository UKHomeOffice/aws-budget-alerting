"""pytest configuration
Define fixtures used by the the tests
"""
import pytest
from botocore.stub import Stubber
from botocore import session


STS_CLIENT = session.get_session().create_client('sts')
BUDGETS_CLIENT = session.get_session().create_client('budgets')


@pytest.fixture(autouse=True)
def sts_stub():
    """creates a botcore stub for the AWS STS service

    :return: yields a Stubber for the AWS STS service
    """
    with Stubber(STS_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def budgets_stub():
    """creates a botcore stub for the AWS Budgets service

    :return: yields a Stubber for the AWS Budgets service
    """
    with Stubber(BUDGETS_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
