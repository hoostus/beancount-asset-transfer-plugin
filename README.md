# Beancount Asset Transfer Plugin

A plugin to automatically generate in-kind transfers between two beancount accounts,
while preserving the cost basis and acquistion date.

# Example Usage

```
2021-09-10 custom "transfer" 100 APPL Assets:Schwab Assets:Fidelity
```

# Quick Explanation

When transferring assets in-kind (for example between two brokerages) you want to preserve
the cost basis and acquisition date of each lot. You can do this manually in beancount like so:

```
2021-09-10 * "Transfer APPL from Schwab to Fidelity"
    Assets:Schwab -100 AAPL {10.00 USD, 2018-05-18}
    Assets:Fidelity 100 APPL {10.00 USD, 2018-05-18}
```

But this quickly becomes tedious when you have dozens of lots or are transferring assets
in-kind frequently.

This plugin will do all the tedious work for you.

# Installation

It is easiest to just run this from a git repository directly in your beancount folder.

```
git clone https://github.com/hoostus/beancount-asset-transfer-plugin asset_transfer
```

Then you need to add two lines to your beancount file:

```
option "insert_pythonpath" "TRUE"
```

This adds the current directory to your python path, which allows you
to run beancount plugins that are in the current directory instead of
requiring them to be installed in some global directory.

```
plugin "asset-transfer.transfer"
```

This activates the plugin. **Note: the first part of the plugin name here *asset_transfer*
has to be same as the name of the directory you git cloned into in the first step.** 

# What It Does

Lots from the source account are iterated in LIFO order -- your most recent lots will
the first ones transferred.

A single Transaction will be generated for the entire transfer.

Each Transaction will have a pair of Postings for each lot being transferred.
One debiting the lot from the source account and the other crediting it to the target account.

The Transaction has
* the flag 'T' (for transfer)
* the payee is empty
* the narration "Automatically generated by asset transfer plugin"
* the tag "in-kind-transfer"

# How To Inspect the Generated Transactions

All that happens behind the scenes. If you want to check the generated Transactions
to ensure the right thing is happening you have a couple of options.

One is to just fire up fava or bean-report or bean-query and inspect the two accounts
to make sure they have the lots they are supposed to.

Another way is to use bean-doctor:

```
bean-doctor context my.beanfile 72
```

where *72* is the line number with custom transfer directive.

# How to run the tests

```
python test_transfer.py
```
