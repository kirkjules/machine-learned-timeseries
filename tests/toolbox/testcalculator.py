import unittest
from htp.toolbox import calculator


class TestPosSizeCalc(unittest.TestCase):

    def test_counter_pos_size(self):
        """
        Note: this formula is used when the account denomination currency is
        the counter currency (denominator) for the traded pair.

        Account denomination: USD
        Account amount: $5000
        Stop loss amount: 200 pips
        Traded pair: EUR/USD

        Example:
            Note, 1% of the realised account is the maximum amount risked per
            trade.
            1. Multiply the account balance and maximum amount risked (as a
            percentage) to give the dollar amount risked.
            MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC
            MAX_RISK_ACC_CURR = $5000 * 0.01
            MAX_RISK_ACC_CURR = $50
            2. Divide the amount risked by the trade stop amount in pips to
            give the valuer per pip.
            VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP
            VALUE_PER_PIP = $50 / 200pips
            VALUE_PER_PIP = $0.25 / pip
            3. Multiply the value per pip by a known unit per pip ratio of
            the traded pair, e.g. EUR/USD, to give the position size.
            POSITION_SIZE = VALUE_PER_PIP * [unit / pip]
            POSITION SIZE = $0.25 / pip * [(10K units of EUR/USD) / ($1 / pip)]
            POSITION_SIZE = 2500 units of EUR/USD
        """
        pos_size = calculator.counter_pos_size(ACC_AMOUNT=5000,
                                               STOP=200,
                                               KNOWN_RATIO=0.0001,
                                               RISK_PERC=0.01)
        print(pos_size)
        self.assertEqual(int(pos_size), 2500)

    def test_base_pos_size(self):
        """
        Note: this formula is used when the account denomination currency is
        the base currency (nominator) for the traded pair.

        Account denomination: EUR
        Account amount: €5000
        Stop loss amount: 200 pips
        Traded pair: EUR/USD

        Example:
            Note, 1% of the realised account is the maximum amount risked per
            trade.
            1. Multiply the account balance and maximum amount risked (as a
            percentage) to give the monetary amount risked.
            MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC
            MAX_RISK_ACC_CURR = €5000 * 0.01
            MAX_RISK_ACC_CURR = €50
            2. Convert the amount risked in the account denomination to the
            counter currency.
            MAX_RISK_CNT_CURR = MAX_RISK_ACC_CURR * TARGET_ASK
            MAX_RISK_CNT_CURR = €50 * (EUR/USD 1.5)
            MAX_RISK_CNT_CURR = $75
            3. Divide the amount risked by the trade stop amount in pips to
            give the valuer per pip.
            VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP
            VALUE_PER_PIP = $75 / 200pips
            VALUE_PER_PIP = $0.375 / pip
            4. Multiply the value per pip by a known unit per pip ratio of
            the traded pair, e.g. EUR/USD, to give the position size.
            POSITION_SIZE = VALUE_PER_PIP * [unit / pip]
            POSITION SIZE = $0.375 / pip * [(10K units of EUR/USD) /
            ($1 / pip)]
            POSITION_SIZE = 3750 units of EUR/USD
        """
        pos_size = calculator.base_pos_size(ACC_AMOUNT=5000,
                                            STOP=200,
                                            TARGET_ASK=1.5,
                                            KNOWN_RATIO=0.0001,
                                            RISK_PERC=0.01)
        print(pos_size)
        self.assertEqual(int(pos_size), 3750)

    def test_counter_conv_pos_size(self):
        """
        Note: this formula is used when the account denomination currency is
        the counter currency (denominator) for the conversion pair, composed
        from the target counter currency against the account currency.

        Account denomination: USD
        Account amount: 5000
        Stop loss amount: 200 pips
        Traded pair: EUR/GBP
        Conversion pair: GBP/USD

        Example:
            Note, 1% of the realised account is the maximum amount risked per
            trade.
            1. Multiply the account balance and maximum amount risked (as a
            percentage) to give the monetary amount risked.
            MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC
            MAX_RISK_ACC_CURR = $5000 * 0.01
            MAX_RISK_ACC_CURR = $50
            2. Convert the amount risked in the account denomination to the
            target counter currency by multiplying by the inverse of the
            conversion pair rate.
            MAX_RISK_CNT_CURR = MAX_RISK_ACC_CURR * CONV_ASK
            MAX_RISK_CNT_CURR = $50 * (1 / GBP/USD 1.75)
            MAX_RISK_CNT_CURR = £28.57
            3. Divide the amount risked by the trade stop amount in pips to
            give the valuer per pip.
            VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP
            VALUE_PER_PIP = £28.57 / 200pips
            VALUE_PER_PIP = £0.14 / pip
            4. Multiply the value per pip by a known unit per pip ratio of
            the traded pair, e.g. EUR/GBP, to give the position size.
            POSITION_SIZE = VALUE_PER_PIP * [unit / pip]
            POSITION SIZE = £0.14 / pip * [(10K units of EUR/GBP) /
            (£1 / pip)]
            POSITION_SIZE = 1429 units of EUR/GBP
        """
        pos_size = calculator.counter_conv_pos_size(ACC_AMOUNT=5000,
                                                    CONV_ASK=1.75,
                                                    STOP=200,
                                                    KNOWN_RATIO=0.0001,
                                                    RISK_PERC=0.01)
        print(pos_size)
        self.assertEqual(int(pos_size), 1429)

    def test_base_conv_pos_size(self):
        """
        Note: this formula is used when the account denomination currency is
        the base currency (nominator) for the conversion pair, composed
        from the account currency against the target counter currency.

        Account denomination: CHF
        Account amount: 5000
        Stop loss amount: 100 pips
        Traded pair: USD/JPY
        Conversion pair: CHF/JPY

        Example:
            Note, 1% of the realised account is the maximum amount risked per
            trade.
            1. Multiply the account balance and maximum amount risked (as a
            percentage) to give the monetary amount risked.
            MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC
            MAX_RISK_ACC_CURR = F5000 * 0.01
            MAX_RISK_ACC_CURR = F50
            2. Convert the amount risked in the account denomination to the
            target counter currency by multiplying by the inverse of the
            conversion pair rate.
            MAX_RISK_CNT_CURR = MAX_RISK_ACC_CURR * CONV_ASK
            MAX_RISK_CNT_CURR = F50 * (1 / CHF/JPY 85)
            MAX_RISK_CNT_CURR = ¥4250
            3. Divide the amount risked by the trade stop amount in pips to
            give the valuer per pip.
            VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP
            VALUE_PER_PIP = ¥4250 / 100pips
            VALUE_PER_PIP = ¥42.5 / pip
            4. Multiply the value per pip by a known unit per pip ratio of
            the traded pair, e.g. EUR/GBP, to give the position size.
            POSITION_SIZE = VALUE_PER_PIP * [unit / pip]
            POSITION SIZE = ¥42.5 / pip * [(100 units of USD/JPY) /
            (¥1 / pip)]
            POSITION_SIZE = 4250 units of EUR/GBP
        """
        pos_size = calculator.base_conv_pos_size(ACC_AMOUNT=5000,
                                                 CONV_ASK=85,
                                                 STOP=100,
                                                 KNOWN_RATIO=0.01,
                                                 RISK_PERC=0.01)
        print(pos_size)
        self.assertEqual(int(pos_size), 4250)

    def test_profit_loss(self):
        """
        Account denomination: USD
        Traded pair: GBP/CHF
        Conversion pair: CHF/USD
        Entry: 2.1443
        Exit: 2.1452

        Profit = (2.1452 - 2.1443) * (1.1025) * 1000
        Profit = 0.99225
        """
        profit_loss_amount = calculator.profit_loss(ENTRY=2.1443,
                                                    EXIT=2.1452,
                                                    POS_SIZE=1000,
                                                    CONV_ASK=1.1025,
                                                    CNT=1)
        print(profit_loss_amount)
        self.assertEqual("0.99225", str(profit_loss_amount))
