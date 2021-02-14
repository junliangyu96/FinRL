import pandas as pd
import numpy as np
from copy import copy
import datetime


class Ledger:

    """
    This class allows for the buying and selling of assets,
    primarily now it will assist in determining tax implications of sales.

    In the future, it could be used to track environment information in an enhanced way.
    """

    def __init__(self, assets, df=None, tax_threshold_days=365):
        self.assets = assets
        self.d = {a: {} for a in assets}
        self.tax_threshold_days = tax_threshold_days
        self.dates = []

    def date_from_str(self, datestr):
        return pd.to_datetime(datestr, infer_datetime_format=True).date()

    def date_to_str(self, date):
        return str(date)

    def log_date(self, date, transactions):

        if isinstance(date, datetime.date):
            date = self.date_to_str(date)

        assert isinstance(date, str)
        if date not in self.dates:
            self.dates.append(self.date_from_str(date))
        tax_d = {}
        for i, (a, t) in enumerate(zip(self.assets, transactions)):
            buys, sells = max(0, t), -min(0, t)

            self.d[a][date] = {"buys": buys, "sells": sells, "tax_used": 0}
            if sells > 0:  # consider order here
                tax_d[i] = self.compute_tax_lots(a, sells, date)
        return tax_d

    def get_longterm_holdings(self):
        # given all assets to date, figure out what the available long term and short term tax options are
        l = [0 for _ in self.assets]
        before_dates = [
            x
            for x in self.dates
            if (self.dates[-1] - datetime.timedelta(self.tax_threshold_days)) > x
        ]
        for i, a in enumerate(self.assets):
            for d in before_dates:
                d = self.date_to_str(d)
                l[i] += self.d[a][d]["buys"] - self.d[a][d]["tax_used"]
        return l

    def compute_tax_lots(self, asset, sells, sell_date):
        a_data = copy(self.d[asset])
        remaining_shares = sells
        long_shares = 0
        short_shares = 0
        # ok, let's loop here and use up shares oldest to youngest
        dates = sorted(a_data)
        i = 0
        while remaining_shares > 0:
            date = dates[i]
            long_term = (
                self.date_from_str(sell_date)
                - datetime.timedelta(days=self.tax_threshold_days)
            ) > self.date_from_str(date)

            d = a_data[date]
            avail_shares = d["buys"] - d["tax_used"]
            if avail_shares > 0:
                # let's consume these
                if avail_shares < remaining_shares:
                    shares_consumed = avail_shares
                else:
                    shares_consumed = remaining_shares

                remaining_shares -= shares_consumed
                if long_term:
                    long_shares += shares_consumed
                else:
                    short_shares += shares_consumed

                a_data[date]["tax_used"] = shares_consumed
            i += 1

        self.d[asset] = a_data
        return {
            "asset": asset,
            "long_term_shares": long_shares,
            "short_term_shares": short_shares,
        }