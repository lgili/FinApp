"""
Monthly Tax Report Use Case.

Computes Brazilian monthly capital gains tax (IR) summary, including
sales exemptions, loss carryover, and DARF base calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Tuple

from finlite.domain.entities.transaction import Transaction
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork

DECIMAL_ZERO = Decimal("0")
DECIMAL_RATE = Decimal("0.15")  # 15% capital gains tax
EARLIEST_DATE = date(2000, 1, 1)


@dataclass(frozen=True)
class GenerateMonthlyTaxReportCommand:
    """Parameters for generating the monthly tax report."""

    month: date  # First day of month
    currency: str = "BRL"


@dataclass(frozen=True)
class MonthlyTaxBreakdown:
    """Detailed tax calculation for the month."""

    month: date
    currency: str
    total_sales: Decimal
    exempt_sales: Decimal
    gains: Decimal
    losses: Decimal
    loss_carry_in: Decimal
    loss_carry_applied: Decimal
    loss_carry_out: Decimal
    taxable_base: Decimal
    darf_rate: Decimal
    darf_tax_due: Decimal
    withheld_tax: Decimal
    darf_tax_payable: Decimal
    dividends: Decimal
    jcp: Decimal

    def rounded_tax_due(self) -> Decimal:
        """Return DARF tax payable rounded to 2 decimals."""
        return self.darf_tax_payable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class MonthlyTaxReport:
    """Result container for the use case."""

    breakdown: MonthlyTaxBreakdown


class MonthlyTaxReportUseCase:
    """Aggregate ledger tax metadata and compute monthly IR summary."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, command: GenerateMonthlyTaxReportCommand) -> MonthlyTaxReport:
        month_start = date(command.month.year, command.month.month, 1)
        month_end = self._end_of_month(month_start)
        currency = command.currency.upper()

        with self._uow:
            transactions = self._uow.transactions.find_by_date_range(
                start_date=EARLIEST_DATE,
                end_date=month_end,
            )

        monthly_events = self._collect_monthly_events(transactions, currency)
        months_sorted = sorted(monthly_events.keys())

        carryover = DECIMAL_ZERO
        breakdown: MonthlyTaxBreakdown | None = None

        for event_month in months_sorted:
            data = monthly_events[event_month]
            loss_carry_in = carryover
            total_sales = data["sales"]
            gains = data["gains"]
            losses = data["losses"]
            dividends = data["dividends"]
            jcp = data["jcp"]
            withheld = data["withheld"]

            exempt_sales = DECIMAL_ZERO
            taxable_base = DECIMAL_ZERO
            loss_carry_applied = DECIMAL_ZERO

            if total_sales <= Decimal("20000"):
                exempt_sales = total_sales
                carryover = carryover + losses
            else:
                net_gain = gains - losses
                if net_gain > DECIMAL_ZERO:
                    if carryover >= net_gain:
                        loss_carry_applied = net_gain
                        taxable_base = DECIMAL_ZERO
                        carryover = carryover - net_gain
                    else:
                        loss_carry_applied = carryover
                        taxable_base = net_gain - carryover
                        carryover = DECIMAL_ZERO
                else:
                    carryover = carryover + abs(net_gain)

            darf_tax_due = (taxable_base * DECIMAL_RATE).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            darf_tax_payable = max(darf_tax_due - withheld, DECIMAL_ZERO)

            current_breakdown = MonthlyTaxBreakdown(
                month=date(event_month[0], event_month[1], 1),
                currency=currency,
                total_sales=total_sales,
                exempt_sales=exempt_sales,
                gains=gains,
                losses=losses,
                loss_carry_in=loss_carry_in,
                loss_carry_applied=loss_carry_applied,
                loss_carry_out=carryover,
                taxable_base=taxable_base,
                darf_rate=DECIMAL_RATE,
                darf_tax_due=darf_tax_due,
                withheld_tax=withheld,
                darf_tax_payable=darf_tax_payable,
                dividends=dividends,
                jcp=jcp,
            )

            if current_breakdown.month == month_start:
                breakdown = current_breakdown

        if breakdown is None:
            breakdown = MonthlyTaxBreakdown(
                month=month_start,
                currency=currency,
                total_sales=DECIMAL_ZERO,
                exempt_sales=DECIMAL_ZERO,
                gains=DECIMAL_ZERO,
                losses=DECIMAL_ZERO,
                loss_carry_in=DECIMAL_ZERO,
                loss_carry_applied=DECIMAL_ZERO,
                loss_carry_out=carryover,
                taxable_base=DECIMAL_ZERO,
                darf_rate=DECIMAL_RATE,
                darf_tax_due=DECIMAL_ZERO,
                withheld_tax=DECIMAL_ZERO,
                darf_tax_payable=DECIMAL_ZERO,
                dividends=DECIMAL_ZERO,
                jcp=DECIMAL_ZERO,
            )

        return MonthlyTaxReport(breakdown=breakdown)

    @staticmethod
    def _end_of_month(month_start: date) -> date:
        if month_start.month == 12:
            return date(month_start.year, 12, 31)
        next_month = date(month_start.year, month_start.month + 1, 1)
        return next_month - timedelta(days=1)

    def _collect_monthly_events(
        self,
        transactions: Iterable[Transaction],
        currency: str,
    ) -> Dict[Tuple[int, int], Dict[str, Decimal]]:
        from decimal import Decimal as D
        from collections import defaultdict

        monthly: Dict[Tuple[int, int], Dict[str, Decimal]] = defaultdict(
            lambda: {
                "sales": DECIMAL_ZERO,
                "gains": DECIMAL_ZERO,
                "losses": DECIMAL_ZERO,
                "dividends": DECIMAL_ZERO,
                "jcp": DECIMAL_ZERO,
                "withheld": DECIMAL_ZERO,
            }
        )

        for txn in transactions:
            if txn.date is None:
                continue
            month_key = (txn.date.year, txn.date.month)
            tag_data = self._parse_tax_tags(txn.tags or ())
            if not tag_data:
                continue

            if "currency" in tag_data and tag_data["currency"].upper() != currency:
                continue

            def as_decimal(value: str) -> Decimal:
                try:
                    return D(value)
                except Exception:
                    return DECIMAL_ZERO

            mref = monthly[month_key]
            if "sale" in tag_data:
                mref["sales"] += as_decimal(tag_data["sale"])
            if "gain" in tag_data:
                mref["gains"] += as_decimal(tag_data["gain"])
            if "loss" in tag_data:
                mref["losses"] += as_decimal(tag_data["loss"])
            if "dividend" in tag_data:
                mref["dividends"] += as_decimal(tag_data["dividend"])
            if "jcp" in tag_data:
                mref["jcp"] += as_decimal(tag_data["jcp"])
            if "withheld" in tag_data:
                mref["withheld"] += as_decimal(tag_data["withheld"])

        return monthly

    @staticmethod
    def _parse_tax_tags(tags: Iterable[str]) -> Dict[str, str]:
        parsed: Dict[str, str] = {}
        for tag in tags:
            if not tag.lower().startswith("tax:"):
                continue
            _, payload = tag.split(":", 1)
            if "=" not in payload:
                continue
            key, value = payload.split("=", 1)
            parsed[key.strip().lower()] = value.strip()
        return parsed
