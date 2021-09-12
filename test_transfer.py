from collections import defaultdict
import unittest
import transfer
from beancount import loader
import beancount.query.query

def get_holdings_by_account(entries, options_map):
    (rtypes, rrows) = beancount.query.query.run_query(entries, options_map, """
        SELECT account,
        units(sum(position)) as units,
        cost_number as cost,
        first(getprice(currency, cost_currency)) as price,
        cost(sum(position)) as book_value,
        value(sum(position)) as market_value,
        cost_date as acquisition_date
        GROUP BY account, cost_date, currency, cost_currency, cost_number
        ORDER BY currency, cost_date
    """)

    accounts = defaultdict(list)
    for r in rrows:
        accounts[r.account].append(r)
    return accounts

class TestTransfer(unittest.TestCase):
    
    @loader.load_doc()
    def test_one(self, entries, _, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {5.00 USD}
            Assets:New-Brokerage 3 VWO {7.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 1 VTI Assets:Brokerage Assets:New-Brokerage
        """

        h = get_holdings_by_account(entries, options_map)

        self.assertEqual('()', str(h['Assets:Brokerage'][0].units))

        self.assertEqual(2, len(h['Assets:New-Brokerage']))
        a = h['Assets:New-Brokerage'][0]
        self.assertEqual('(1 VTI)', str(a.units))
        self.assertEqual('2021-01-01', str(a.acquisition_date))
        self.assertEqual('(5.00 USD)', str(a.book_value))

    @loader.load_doc()
    def test_multi(self, entries, _, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 5 VTI"
            Assets:Brokerage 5 VTI {5.00 USD}
            Assets:New-Brokerage 3 VWO {55.00 USD}
            Assets:Bank

        2021-01-02 * "Buy 2 VTI"
            Assets:Brokerage 2 VTI {6.00 USD}
            Assets:Bank

        2021-01-03 * "Buy 3 VTI"
            Assets:Brokerage 3 VTI {7.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 4 VTI Assets:Brokerage Assets:New-Brokerage
        """

        all_accounts = get_holdings_by_account(entries, options_map)
        brokerage = sorted(all_accounts['Assets:Brokerage'], key=lambda a: a.acquisition_date)
        self.assertEqual('(5 VTI)', str(brokerage[0].units))
        self.assertEqual('(1 VTI)', str(brokerage[1].units))
        self.assertEqual('2021-01-02', str(brokerage[1].acquisition_date))

        new_brokerage = sorted(all_accounts['Assets:New-Brokerage'], key=lambda a: a.acquisition_date)
        self.assertEqual(3, len(new_brokerage))
        # the preexisting VWO lot
        lot1 = new_brokerage[0]
        self.assertEqual('(3 VWO)', str(lot1.units))
        self.assertEqual('2021-01-01', str(lot1.acquisition_date))

        # transferred VTI lots
        lot2 = new_brokerage[1]
        self.assertEqual('(1 VTI)', str(lot2.units))
        self.assertEqual('2021-01-02', str(lot2.acquisition_date))
        lot3 = new_brokerage[2]
        self.assertEqual('(3 VTI)', str(lot3.units))
        self.assertEqual('2021-01-03', str(lot3.acquisition_date))

    @loader.load_doc(expect_errors=True)
    def test_error_paramcount(self, entries, errors, option_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Asset transfer requires 3 parameters", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_amount(self, entries, errors, option_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 12 Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("valid beancount Amount", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_src(self, entries, errors, option_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 1 VTI 0 Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Source account for transfer does not appear to be an account", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_dest(self, entries, errors, option_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 1 VTI Assets:Brokerage 0
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Destination account for transfer does not appear to be an account", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_insufficient(self, entries, errors, option_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-05 custom "transfer" 100 VTI Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Expected 99 more.", errors[0].message)

if __name__ == '__main__':
    unittest.main()