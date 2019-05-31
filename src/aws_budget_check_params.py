"""Module checking that budget and threshold parameters are valid.
If the actual and forecasted trigger thresholds are below the actual budget, alerting will never
occur.
"""

from os import path
from dataclasses import dataclass
import sys
import logging
import boto3


class InvalidPercentageException(Exception):
    """Exception indicating that a number is not a valid percentage (<0)
    """


@dataclass
class Budget:
    """Class specifying information about the AWS Budget
    """
    limit_amount: float  # budget limit amount
    calculated_actual_spend: float
    calculated_forecasted_spend: float


class AwsBudgetThresholdchecker:
    """Class allowing to check the thresholds set for an AWS Budget.
    """

    def __init__(self, sts_client, budgets_client, budget_name):
        """Constructor

        :param sts_client: (boto3.client) 'sts' boto3 client
        :param budgets_client: (boto3.client) 'budgets' boto3 client
        :param budget_name: the name of the budget that should be checked
        """
        self.budget_name = budget_name
        self.account_id = sts_client.get_caller_identity().get('Account')
        self.budgets_client = budgets_client

    def check_threshold_trigger(self, actual_threshold_percentage, forecasted_threshold_percentage):
        """Checks if a given threshold is higher than the value it is going to be compared to.
        If it is not, an alert would not occur during the current period.
        In most cases, we don't want that to happen and would want to be warned about it, although
        it might be valid in certain cases

        :param actual_threshold_percentage: () the actual threshold percentage that should trigger
            an alert
        :param forecasted_threshold_percentage: () the forecasted threshold percentage that should
            trigger an alert
        :return: (bool) true if the threshold is high enough to potentially result in a trigger
            if the conditions are met in the current period
        """
        budget = self.get_budget()
        passed = True
        if actual_threshold_percentage <= 0:
            raise InvalidPercentageException(f"actual_threshold_percentage should be >0 (got "
                                             f"{actual_threshold_percentage})")
        if forecasted_threshold_percentage <= 0:
            raise InvalidPercentageException(f"forecasted should be >0 (got "
                                             f"{forecasted_threshold_percentage})")
        actual_threshold_trigger = actual_threshold_percentage / 100 * budget.limit_amount
        if actual_threshold_trigger < budget.calculated_actual_spend:
            passed = False
            logging.warning("warning: actual threshold trigger (%s) < "
                            "calculated actual spend (%s)", actual_threshold_trigger,
                            budget.calculated_actual_spend)
        forecasted_threshold_trigger = \
            forecasted_threshold_percentage / 100 * budget.limit_amount
        if forecasted_threshold_trigger < budget.calculated_forecasted_spend:
            passed = False
            logging.warning(
                "warning: forecasted threshold trigger (%s) < "
                "calculated forecasted spend (%s)", forecasted_threshold_trigger,
                budget.calculated_forecasted_spend)
        return passed

    def get_budget(self):
        """Gets info about the AWS Budget we're dealing with

        :return: a Budget object
        """
        budget_resp = self.budgets_client.describe_budget(
            AccountId=self.account_id,
            BudgetName=self.budget_name,
        )
        logging.debug(budget_resp)
        limit_amount = float(budget_resp['Budget']['BudgetLimit']['Amount'])
        time_unit = budget_resp['Budget']['TimeUnit']
        calculated_actual_spend = float(budget_resp['Budget']['CalculatedSpend']
                                        ['ActualSpend']['Amount'])
        calculated_forecasted_spend = float(budget_resp['Budget']['CalculatedSpend']
                                            ['ForecastedSpend']['Amount'])
        logging.info("budget amount: %s", limit_amount)
        logging.info("time limit: %s", time_unit)
        logging.info("calculated actual spend: %s", calculated_actual_spend)
        logging.info("calculated forecasted spend: %s", calculated_forecasted_spend)
        return Budget(limit_amount=limit_amount,
                      calculated_actual_spend=calculated_actual_spend,
                      calculated_forecasted_spend=calculated_forecasted_spend,
                      )


def usage():
    """prints the script's usage

    :return: None
    """

    print(
        f"usage: {path.basename(__file__)} BUDGET_NAME ACTUAL_THRESHOLD_PERCENTAGE FORECASTED_"
        f"THRESHOLD_PERCENTAGE\n"
        f"Checks the values of the budget thresholds against the current and forecasted values.\n"
        f"The checks fail if the thresholds are too low and would never cause an alert in the \n"
        f"current period.\n"
        f"\n"
        f"where:\n"
        f"\n"
        f"BUDGET_NAME is the monthly budget for all AWS costs for the account\n"
        f"ACTUAL_THRESHOLD_PERCENTAGE is the percentage of the budget that should trigger alerts "
        f"for\n"
        f"    actual costs\n"
        f"FORECASTED_THRESHOLD_PERCENTAGE is the percentage of the budget that should trigger "
        f"alerts\n"
        f"    for forecasted costs\n"
    )


def main():
    """Main entry point
    """
    if len(sys.argv) != 4:
        usage()
        sys.exit(-1)
    budget_name = sys.argv[1]
    actual_threshold_percentage = int(sys.argv[2])
    forecasted_threshold_percentage = int(sys.argv[3])

    if logging.getLogger(__name__).level > logging.INFO:
        logging.basicConfig(level=logging.INFO)

    sts_client = boto3.client('sts')
    budgets_client = boto3.client('budgets')

    try:
        check_passed = AwsBudgetThresholdchecker(
            sts_client=sts_client,
            budgets_client=budgets_client,
            budget_name=budget_name,
        ).check_threshold_trigger(
            actual_threshold_percentage=actual_threshold_percentage,
            forecasted_threshold_percentage=forecasted_threshold_percentage,
        )
        logging.info("threshold check passed: %s", check_passed)
    except InvalidPercentageException as ipe:
        print(str(ipe))
        sys.exit(-2)
    if check_passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
