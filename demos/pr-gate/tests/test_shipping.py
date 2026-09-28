"""Regression coverage for customer-visible shipping fees."""

from __future__ import annotations

import unittest

from storefront.shipping import shipping_fee_cents


class ShippingFeeTests(unittest.TestCase):
    def test_vip_shipping_is_free_below_the_standard_threshold(self) -> None:
        self.assertEqual(shipping_fee_cents(1_200, is_vip=True), 0)

    def test_standard_order_below_threshold_pays_shipping(self) -> None:
        self.assertEqual(shipping_fee_cents(1_200), 1_500)

    def test_standard_order_at_threshold_gets_free_shipping(self) -> None:
        self.assertEqual(shipping_fee_cents(5_000), 0)

    def test_standard_order_above_threshold_gets_free_shipping(self) -> None:
        self.assertEqual(shipping_fee_cents(7_500), 0)


if __name__ == "__main__":
    unittest.main()
