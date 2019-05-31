"""Tests for the AwsBudgetThresholdchecker class
"""
import pytest
from botocore.exceptions import ClientError
from aws_budget_check_params import AwsBudgetThresholdchecker
from .conftest import BUDGETS_CLIENT, STS_CLIENT


def get_budget_response(budget_name, budget_limit_amount, calculated_actual_spend,
                        calculated_forecasted_spend):
    """Returns a mocked response object for the get_budget call

    :param budget_name: (str) the budget name
    :param budget_limit_amount: (float) the budget value
    :param calculated_actual_spend: (float) the current actual spend
    :param calculated_forecasted_spend: (float) the forecasted cost according to AWS
    :return: the response object
    """
    return {
        "Budget": {
            "BudgetName": budget_name,
            "BudgetLimit": {
                "Amount": str(budget_limit_amount),
                "Unit": "USD"
            },
            "CostTypes": {
                "IncludeTax": True,
                "IncludeSubscription": True,
                "UseBlended": False,
                "IncludeRefund": True,
                "IncludeCredit": True,
                "IncludeUpfront": True,
                "IncludeRecurring": True,
                "IncludeOtherSubscription": True,
                "IncludeSupport": True,
                "IncludeDiscount": True,
                "UseAmortized": False
            },
            "TimeUnit": "MONTHLY",
            "TimePeriod": {
                "Start": 1556668800.0,
                "End": 3706473600.0
            },
            "CalculatedSpend": {
                "ActualSpend": {
                    "Amount": str(calculated_actual_spend),
                    "Unit": "USD"
                },
                "ForecastedSpend": {
                    "Amount": str(calculated_forecasted_spend),
                    "Unit": "USD"
                }
            },
            "BudgetType": "COST",
            "LastUpdatedTime": 1559530911.092
        }
    }


def test_awsbudgetthresholdchecker_checkthresholdtrigger_incorrent_bucket_name_exception(
        sts_stub,
        budgets_stub):
    """ Tests that AwsBudgetThresholdchecker throws an exception if the budget name does not exist.

    :param sts_stub: (Stubber) the fixture providing a stub for the AWS STS service
    :param budgets_stub: (Stubber) the fixture providing a stub for the AWS Budgets service
    :return: None
    """
    account_id = '123456789012'

    sts_response = {
        'Account': account_id,
    }
    sts_stub.add_response('get_caller_identity', sts_response, {})

    budgets_stub.add_client_error('describe_budget')
    with pytest.raises(ClientError):
        assert AwsBudgetThresholdchecker(
            sts_client=STS_CLIENT, budgets_client=BUDGETS_CLIENT,
            budget_name='budget-that-does-not-exist',
        ).check_threshold_trigger(
            actual_threshold_percentage=100,
            forecasted_threshold_percentage=110,
        )


def test_awsbudgetthresholdchecker_checkthresholdtrigger_actual_low_thresholds(sts_stub,
                                                                               budgets_stub):
    """ Tests that AwsBudgetThresholdchecker.check_threshold_trigger returns False when the
    actual threshold percentage is too low to trigger an alert

    :param sts_stub: (Stubber) the fixture providing a stub for the AWS STS service
    :param budgets_stub: (Stubber) the fixture providing a stub for the AWS Budgets service
    :return: None
    """
    budget_name = 'my-budget'
    account_id = '123456789012'

    sts_response = {
        'Account': account_id,
    }
    sts_stub.add_response('get_caller_identity', sts_response, {})

    budgets_expected_params = {
        'AccountId': account_id,
        'BudgetName': budget_name,
    }
    budget_response = get_budget_response(budget_name=budget_name, budget_limit_amount=100,
                                          calculated_actual_spend=90,
                                          calculated_forecasted_spend=100)
    budgets_stub.add_response('describe_budget', budget_response,
                              expected_params=budgets_expected_params)
    assert AwsBudgetThresholdchecker(
        sts_client=STS_CLIENT, budgets_client=BUDGETS_CLIENT,
        budget_name=budget_name,
    ).check_threshold_trigger(
        actual_threshold_percentage=10,
        forecasted_threshold_percentage=110,
    ) is False


def test_awsbudgetthresholdchecker_checkthresholdtrigger_forecasted_low_thresholds(sts_stub,
                                                                                   budgets_stub):
    """ Tests that AwsBudgetThresholdchecker.check_threshold_trigger returns False when the
    forecasted threshold percentage is too low to trigger an alert

    :param sts_stub: (Stubber) the fixture providing a stub for the AWS STS service
    :param budgets_stub: (Stubber) the fixture providing a stub for the AWS Budgets service
    :return: None
    """
    budget_name = 'my-budget'
    account_id = '123456789012'

    sts_response = {
        'Account': account_id,
    }
    sts_stub.add_response('get_caller_identity', sts_response, {})

    budgets_expected_params = {
        'AccountId': account_id,
        'BudgetName': budget_name,
    }
    budget_response = get_budget_response(budget_name=budget_name, budget_limit_amount=100,
                                          calculated_actual_spend=90,
                                          calculated_forecasted_spend=100)
    budgets_stub.add_response('describe_budget', budget_response,
                              expected_params=budgets_expected_params)
    assert AwsBudgetThresholdchecker(
        sts_client=STS_CLIENT, budgets_client=BUDGETS_CLIENT,
        budget_name=budget_name,
    ).check_threshold_trigger(
        actual_threshold_percentage=100,
        forecasted_threshold_percentage=10,
    ) is False


def test_awsbudgetthresholdchecker_checkthresholdtrigger_high_thresholds(sts_stub,
                                                                         budgets_stub):
    """ Tests that AwsBudgetThresholdchecker.check_threshold_trigger returns True when the
    threshold percentages are both high enough to trigger alerts.

    :param sts_stub: (Stubber) the fixture providing a stub for the AWS STS service
    :param budgets_stub: (Stubber) the fixture providing a stub for the AWS Budgets service
    :return: None
    """
    budget_name = 'my-budget'
    account_id = '123456789012'

    sts_response = {
        'Account': account_id,
    }
    sts_stub.add_response('get_caller_identity', sts_response, {})

    budgets_expected_params = {
        'AccountId': account_id,
        'BudgetName': budget_name,
    }
    budget_response = get_budget_response(budget_name=budget_name, budget_limit_amount=100,
                                          calculated_actual_spend=90,
                                          calculated_forecasted_spend=100)
    budgets_stub.add_response('describe_budget', budget_response,
                              expected_params=budgets_expected_params)
    assert AwsBudgetThresholdchecker(
        sts_client=STS_CLIENT, budgets_client=BUDGETS_CLIENT,
        budget_name=budget_name,
    ).check_threshold_trigger(
        actual_threshold_percentage=100,
        forecasted_threshold_percentage=110,
    ) is True
