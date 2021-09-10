import unittest
import transfer
from beancount import loader

class TestTransfer(unittest.TestCase):
    @loader.load_doc()
    def atest_stuff(self, entries, _, options_map):
        """
        plugin "transfer"
        2021-01-01 open Assets:Brokerage
        2021-01-01 open Assets:Bank
        2021-01-01 open Assets:New-Brokerage

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {100.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" 1 VTI Assets:Brokerage Assets:New-Brokerage
        """

        new_entries, errors = transfer.transfer(entries, options_map)
        self.assertEqual(5, len(new_entries))

    @loader.load_doc(expect_errors=True)
    def test_error_paramcount(self, entries, errors, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Asset transfer requires 3 parameters", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_amount(self, entries, errors, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" 12 Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("valid beancount Amount", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_src(self, entries, errors, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" 1 VTI 0 Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Source account for transfer does not appear to be an account", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_dest(self, entries, errors, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" 1 VTI Assets:Brokerage 0
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Destination account for transfer does not appear to be an account", errors[0].message)

    @loader.load_doc(expect_errors=True)
    def test_error_insufficient(self, entries, errors, options_map):
        """
        plugin "beancount.plugins.auto"
        plugin "transfer"

        2021-01-01 * "Buy 1 VTI"
            Assets:Brokerage 1 VTI {1.00 USD}
            Assets:New-Brokerage 1 VWO {1.00 USD}
            Assets:Bank

        2021-01-01 custom "transfer" 100 VTI Assets:Brokerage Assets:New-Brokerage
        """

        self.assertEqual([transfer.TransferError], list(map(type, errors)))
        self.assertIn("Expected 99 more.", errors[0].message)

if __name__ == '__main__':
    unittest.main()