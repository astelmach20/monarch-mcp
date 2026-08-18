import unittest
from unittest.mock import AsyncMock, patch

from tools.planning import get_cash_flow


def _transaction(amount: float, group_type: str | None, category: str) -> dict:
    group = {"type": group_type} if group_type is not None else None
    return {
        "amount": amount,
        "category": {"name": category, "icon": "#", "group": group},
    }


class GetCashFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_expense_refunds_offset_charges(self) -> None:
        transactions = [
            _transaction(-262.85, "expense", "Electronics"),
            _transaction(262.85, "expense", "Electronics"),
            _transaction(-359.28, "expense", "Electronics"),
            _transaction(359.28, "expense", "Electronics"),
        ]

        with patch(
            "tools.planning.query",
            new=AsyncMock(
                return_value={
                    "data": {"allTransactions": {"results": transactions}}
                }
            ),
        ):
            result = await get_cash_flow("2026-08")

        self.assertEqual(result["expenses"], 0)
        self.assertEqual(result["expenses_by_category"], {})

    async def test_adjustments_keep_their_sign_and_transfers_are_ignored(self) -> None:
        transactions = [
            _transaction(1_000, "income", "Paychecks"),
            _transaction(-50, "income", "Paychecks"),
            _transaction(-100, "expense", "Shopping"),
            _transaction(25, "expense", "Shopping"),
            _transaction(-40, None, "Uncategorized"),
            _transaction(10, None, "Uncategorized"),
            _transaction(-500, "transfer", "Transfer"),
            _transaction(500, "transfer", "Transfer"),
        ]

        with patch(
            "tools.planning.query",
            new=AsyncMock(
                return_value={
                    "data": {"allTransactions": {"results": transactions}}
                }
            ),
        ):
            result = await get_cash_flow("2026-08")

        self.assertEqual(result["income"], 950)
        self.assertEqual(result["expenses"], 105)
        self.assertEqual(result["savings"], 845)
        self.assertEqual(result["income_by_category"], {"# Paychecks": 950})
        self.assertEqual(
            result["expenses_by_category"],
            {"# Shopping": 75, "# Uncategorized": 30},
        )


if __name__ == "__main__":
    unittest.main()
