"""Non-executable semantic contract. All objects reject unknown fields."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Union
import re
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator, model_validator


def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Expected an ISO calendar date string')
    date.fromisoformat(value)
    return value


def numeric_string(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)?', value):
        raise ValueError('Expected a nonnegative finite decimal string, not a JSON number')
    return value


Day = Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$'), BeforeValidator(iso_day)]
Number = Annotated[str, Field(pattern=r'^\d+(?:\.\d+)?$'), BeforeValidator(numeric_string)]
Identifier = Annotated[str, Field(min_length=1, pattern=r'^[A-Za-z0-9_.:-]+$')]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Money(Strict):
    value: Number | None
    currency: Annotated[str, Field(pattern=r'^[A-Z]{3}$')]


class Selector(Strict):
    user_id: Identifier
    category: Identifier
    direction: Literal['debit', 'credit']
    currency: Annotated[str, Field(pattern=r'^[A-Z]{3}$')]
    description: str | None


class StatusPayload(Strict):
    status: Literal['ongoing', 'ended', 'one_time', 'contingent']


class AmountPayload(Strict):
    # A percentage is evidence, not a model-calculated new monetary amount.
    money: Money | None
    percent_increase: Number | None
    scope: Literal['one_cycle', 'ongoing', 'unknown']

    @model_validator(mode='after')
    def exclusive(self):
        if self.money is not None and self.percent_increase is not None:
            raise ValueError('Supply an absolute amount OR a percentage')
        return self


class SchedulePayload(Strict):
    payment_date: Day | None
    cadence: Literal['monthly', 'fixed_days'] | None
    interval_days: Annotated[int, Field(gt=0)] | None
    scope: Literal['one_cycle', 'ongoing', 'unknown']

    @model_validator(mode='after')
    def interval(self):
        if (self.cadence == 'fixed_days') != (self.interval_days is not None):
            raise ValueError('A fixed-day cadence requires an interval, and only it may have one')
        return self


class FuturePayload(Strict):
    money: Money
    payment_date: Day | None
    direction: Literal['debit', 'credit']


class LifecyclePayload(Strict):
    relationship: Literal['cancellation', 'refund_of', 'retry_of', 'settlement_of',
                          'possible_duplicate_of', 'internal_transfer']
    related_event_id: Identifier


class ImagePayload(Strict):
    value_type: Literal['net_pay', 'balance_due', 'current_amount_due', 'amount_paid']
    money: Money
    image_id: Identifier
    selected_field: Annotated[str, Field(min_length=1)]


class CashPayload(Strict):
    classification: Literal['cash', 'non_cash_valuation', 'pending_credit',
                            'contingent_income', 'historical_only']


class FactBase(Strict):
    schema_version: Literal['1.0']
    fact_id: Identifier
    evidence_ids: Annotated[list[Identifier], Field(min_length=1)]
    affected_event_ids: list[Identifier]
    stream_selector: Selector | None
    effective_from: Day | None
    effective_until: Day | None
    confirmation_state: Literal['confirmed', 'uncertain']
    unresolved_fields: list[str]

    @model_validator(mode='after')
    def target_and_range(self):
        if not self.affected_event_ids and self.stream_selector is None:
            raise ValueError('An event or structured stream target is required')
        if self.effective_from and self.effective_until and self.effective_from > self.effective_until:
            raise ValueError('Reversed effective range')
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError('Duplicate evidence IDs')
        return self


class StreamStatus(FactBase):
    fact_type: Literal['stream_status']
    payload: StatusPayload


class AmountAmendment(FactBase):
    fact_type: Literal['amount_amendment']
    payload: AmountPayload


class ScheduleAmendment(FactBase):
    fact_type: Literal['date_or_schedule_amendment']
    payload: SchedulePayload


class FutureConfirmation(FactBase):
    fact_type: Literal['future_event_confirmation']
    payload: FuturePayload


class Lifecycle(FactBase):
    fact_type: Literal['lifecycle_relationship']
    payload: LifecyclePayload


class ImageValue(FactBase):
    fact_type: Literal['image_financial_value']
    payload: ImagePayload


class CashClassification(FactBase):
    fact_type: Literal['cash_classification']
    payload: CashPayload


Fact = Annotated[Union[StreamStatus, AmountAmendment, ScheduleAmendment,
                       FutureConfirmation, Lifecycle, ImageValue, CashClassification],
                 Field(discriminator='fact_type')]


class EvidenceBundle(Strict):
    facts: list[Fact]

    @model_validator(mode='after')
    def unique_ids(self):
        if len({f.fact_id for f in self.facts}) != len(self.facts):
            raise ValueError('Duplicate fact IDs')
        return self
