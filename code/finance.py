"""Deterministic state, recurrence and ledger. No model calls or sample IDs."""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
import calendar

from evidence import (StreamStatus, AmountAmendment, ScheduleAmendment,
                       FutureConfirmation, Lifecycle, ImageValue, CashClassification)

D = Decimal
ZERO = D('0')
CENT = D('.01')


def day(value):
    return date.fromisoformat(value)


def decimal(value):
    if isinstance(value, float):
        raise ValueError('Float money is forbidden')
    result = D(value)
    if not result.is_finite():
        raise ValueError('Non-finite money')
    return result


def add_months(value, months=1, dom=None, eom=False):
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, last if eom else min(dom or value.day, last))


@dataclass
class Event:
    id: str
    user: str
    category: str
    description: str
    direction: str
    amount: Decimal | None
    currency: str
    event_date: date
    settlement: date | None
    status: str
    event_type: str
    linked: str
    flexibility: str
    minimum: Decimal | None
    excluded: str | None = None
    history_excluded: bool = False
    evidence: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)


@dataclass
class Stream:
    id: str
    history: list[Event]
    amount: Decimal
    monthly: bool
    step: int
    dom: int
    eom: bool
    last: date
    amendments: list = field(default_factory=list)

    @property
    def anchor(self):
        return self.history[-1]


@dataclass
class Flow:
    when: date
    amount: Decimal  # signed, home currency
    source: str
    provenance: str
    evidence: list[str]
    policy: list[str]
    stream_id: str | None = None
    native_amount: Decimal | None = None
    currency: str | None = None
    fx_date: date | None = None


@dataclass
class State:
    profile: dict
    request: dict
    events: list[Event]
    facts: list
    issues: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    streams: list[Stream] = field(default_factory=list)
    flows: list[Flow] = field(default_factory=list)

    @property
    def start(self): return day(self.request['request_date'])

    @property
    def end(self): return self.start + timedelta(days=89)


def targets(fact, event):
    # Explicit targets restrict rather than expand a selector's scope.
    if fact.affected_event_ids:
        return event.id in fact.affected_event_ids
    s = fact.stream_selector
    return bool(s and s.user_id == event.user and s.category == event.category
                and s.direction == event.direction and s.currency == event.currency
                and (s.description is None or s.description == event.description))


def applicable(fact, when):
    return ((fact.effective_from is None or day(fact.effective_from) <= when)
            and (fact.effective_until is None or when <= day(fact.effective_until)))


def resolve(raw, profile, request, facts, evidence_index):
    facts=sorted(facts,key=lambda f:f.fact_id)
    events = [Event(e['event_id'], e['user_id'], e['category'], e['description'], e['direction'],
                    decimal(e['amount']) if e['amount'] else None, e['currency'],
                    day(e['event_date']), day(e['settlement_date']) if e['settlement_date'] else None,
                    e['status'], e['event_type'], e['linked_event_id'], e['flexibility'],
                    decimal(e['minimum_allowed_amount']) if e['minimum_allowed_amount'] else None,
                    evidence=[e['event_id']]) for e in raw]
    if any(e.user != request['user_id'] for e in events):
        raise ValueError('Cross-user raw events')
    state = State(profile, request, events, facts)
    ids = {e.id: e for e in events}
    if len(ids) != len(events): raise ValueError('Duplicate event ID')
    # Detect competing explicit writes before mutation; ordering is not precedence.
    claims=defaultdict(list)
    for f in facts:
        if f.confirmation_state!='confirmed':continue
        for identifier in f.affected_event_ids:
            if isinstance(f,AmountAmendment) and f.stream_selector is None:
                claims[(identifier,'amount')].append((f,repr(f.payload.model_dump())))
            elif isinstance(f,ImageValue) and f.payload.value_type!='amount_paid':
                claims[(identifier,'amount')].append((f,repr(f.payload.money.model_dump())))
            elif isinstance(f,FutureConfirmation):
                claims[(identifier,'amount')].append((f,repr(f.payload.money.model_dump())))
                claims[(identifier,'date')].append((f,str(f.payload.payment_date)))
            elif isinstance(f,ScheduleAmendment) and f.stream_selector is None:
                claims[(identifier,'date')].append((f,str(f.payload.payment_date)))
    rejected=set()
    for (identifier,field_name),values in sorted(claims.items()):
        if len({value for _,value in values})>1:
            rejected.update(f.fact_id for f,_ in values)
            state.blockers.append(f'{identifier}: conflicting explicit {field_name} facts')
    for f in facts:
        for identifier in f.evidence_ids:
            source = evidence_index.get(identifier)
            if source is None or source['user_id'] != request['user_id']:
                raise ValueError('Missing or cross-user evidence: ' + identifier)
            if source.get('sent_at', '')[:10] > request['request_date']:
                raise ValueError('Future message evidence')
        if any(identifier not in ids for identifier in f.affected_event_ids):
            raise ValueError('Unknown target event')
        if f.stream_selector and f.stream_selector.user_id != request['user_id']:
            raise ValueError('Cross-user selector')
        if f.fact_id in rejected:continue
        if f.confirmation_state != 'confirmed':
            state.issues.append(f'{f.fact_id}: uncertain evidence; no positive cash consequence')
            if isinstance(f, (AmountAmendment, FutureConfirmation, ImageValue)):
                if (any(targets(f,e) and e.direction=='debit' for e in events)
                    or isinstance(f,FutureConfirmation) and f.payload.direction=='debit'
                    or f.stream_selector is not None and f.stream_selector.direction=='debit'):
                    state.blockers.append(f'{f.fact_id}: uncertain obligation amount')
            if isinstance(f,ScheduleAmendment):
                state.blockers.append(f'{f.fact_id}: uncertain schedule retained unresolved')
            continue
        if isinstance(f, ImageValue):
            if f.payload.image_id not in f.evidence_ids:
                raise ValueError('Image provenance missing')
            image_record = evidence_index[f.payload.image_id]
            if image_record.get('related_event_id') not in f.affected_event_ids:
                raise ValueError('Image does not link to targeted event')
            for e in events:
                if not targets(f,e): continue
                if f.payload.money.currency != e.currency: raise ValueError('Image currency mismatch')
                if f.payload.money.value is None:
                    state.issues.append(f'{f.fact_id}: image amount unknown')
                    continue
                # Document value kind is interpreted against the existing event direction.
                if (e.direction=='debit' and f.payload.value_type not in ('balance_due','current_amount_due','amount_paid')) or (e.direction=='credit' and f.payload.value_type!='net_pay'):
                    state.blockers.append(f'{f.fact_id}: incompatible document value')
                    continue
                value = decimal(f.payload.money.value)
                if e.amount is not None and e.amount != value:
                    state.blockers.append(f'{f.fact_id}: conflicting structured/image amount')
                    continue
                if f.payload.value_type=='amount_paid' and (e.status!='settled' or e.settlement is None or e.settlement>=state.start):
                    state.blockers.append(f'{f.fact_id}: amount_paid does not establish an outstanding obligation')
                    continue
                e.amount = value; e.evidence.extend(f.evidence_ids); e.facts.append(f.fact_id)
                state.changes.append(f'{e.id}: missing amount resolved from {f.payload.selected_field}')
        if isinstance(f, CashClassification):
            for e in events:
                if targets(f,e) and applicable(f,e.settlement or state.start) and f.payload.classification != 'cash':
                    e.excluded = f.payload.classification
                    e.facts.append(f.fact_id)
        if isinstance(f, FutureConfirmation) and f.affected_event_ids:
            for identifier in f.affected_event_ids:
                e=ids[identifier]
                if f.payload.direction!=e.direction or f.payload.money.currency!=e.currency:
                    raise ValueError('Future confirmation direction/currency mismatch')
                if f.payload.money.value is None or f.payload.payment_date is None:
                    state.blockers.append(f'{f.fact_id}: incomplete future confirmation');continue
                # A confirmation does not convert an unsettled refund/credit into settled cash.
                if e.status in ('failed','cancelled','unrealized','pending'):
                    state.issues.append(f'{f.fact_id}: cash status retained as {e.status}');continue
                e.amount=decimal(f.payload.money.value);e.settlement=day(f.payload.payment_date)
                e.facts.append(f.fact_id);e.evidence.extend(f.evidence_ids)
        if isinstance(f, Lifecycle):
            parent = ids.get(f.payload.related_event_id)
            if parent is None: raise ValueError('Unknown lifecycle parent')
            relation = f.payload.relationship
            children = [ids[i] for i in f.affected_event_ids]
            if relation == 'possible_duplicate_of':
                state.issues.append(f'{f.fact_id}: possible duplicate retained')
                continue
            elif relation == 'internal_transfer':
                # Scope is trusted structured context, never inferred from "internal".
                legs=[parent]+children
                scope=profile.get('modeled_cash_account_ids',[])
                accounts=[evidence_index.get(e.id,{}).get('account_id') for e in legs]
                balanced=(len(legs)==2 and {e.direction for e in legs}=={'debit','credit'}
                          and legs[0].amount is not None and legs[0].amount==legs[1].amount
                          and legs[0].currency==legs[1].currency
                          and legs[0].settlement is not None and legs[0].settlement==legs[1].settlement
                          and all(e.status=='settled' for e in legs))
                if not (len(set(accounts))==2 and all(a and a in scope for a in accounts) and balanced):
                    state.blockers.append(f'{f.fact_id}: internal transfer cash scope or balanced settlement unestablished')
                    continue
                for e in legs:e.excluded='internal_transfer'
            elif relation == 'cancellation':
                parent.excluded = 'explicit cancellation'
            elif relation in ('settlement_of','retry_of'):
                for child in children:
                    if parent.direction != child.direction: raise ValueError('Lifecycle direction mismatch')
                    if parent.status in ('pending','failed','cancelled') and child.status in ('settled','scheduled'):
                        parent.excluded = relation + ':' + child.id
            # Refund does not erase a settled charge. Each retains its own cash state.
            parent.history_excluded = True
            for child in children: child.history_excluded = True
            state.changes.append(f'{f.fact_id}: lifecycle {relation} resolved by status')
    for e in events:
        if e.linked:
            possible=any(isinstance(f,Lifecycle) and f.payload.relationship=='possible_duplicate_of'
                         and e.id in f.affected_event_ids and f.payload.related_event_id==e.linked for f in facts)
            if not possible:
                e.history_excluded = True
                if e.linked in ids: ids[e.linked].history_excluded = True
            # A link alone never authorizes removal of either cash leg.
            if not any(isinstance(f,Lifecycle) and e.id in f.affected_event_ids for f in facts):
                state.issues.append(f'{e.id}: lifecycle link preserved; no semantic replacement assumed')
        if e.status in ('failed','cancelled','unrealized') or e.direction=='non_cash':
            e.excluded = e.excluded or e.status
        if e.direction=='credit' and e.status=='pending': e.excluded='pending credit'
        if e.excluded: state.changes.append(f'{e.id}: excluded ({e.excluded})')
    for f in facts:
        if f.fact_id in rejected:continue
        if isinstance(f,ScheduleAmendment) and f.confirmation_state=='confirmed' and f.stream_selector is None:
            for identifier in f.affected_event_ids:
                e=ids[identifier]
                if (not f.payload.payment_date or f.payload.cadence is not None or f.effective_until is not None
                    or f.payload.scope!='one_cycle' or e.status not in ('scheduled','pending')
                    or not applicable(f,e.settlement or state.start)):
                    state.blockers.append(f'{f.fact_id}: standalone date amendment unresolved');continue
                e.settlement=day(f.payload.payment_date)
                e.facts.append(f.fact_id);e.evidence.extend(f.evidence_ids)
                state.changes.append(f'{e.id}: explicit date amendment {f.fact_id}')
        if isinstance(f,AmountAmendment) and f.confirmation_state=='confirmed' and f.affected_event_ids and f.stream_selector is None:
            # Explicit event amendments are values, not inference directives.
            for identifier in f.affected_event_ids:
                e=ids[identifier]
                if not applicable(f,e.settlement or state.start):continue
                if f.payload.money and f.payload.money.currency!=e.currency:raise ValueError('Amount currency mismatch')
                if f.payload.money and f.payload.money.value is not None:
                    e.amount=decimal(f.payload.money.value)
                elif f.payload.percent_increase is not None and e.amount is not None:
                    e.amount*=D(1)+decimal(f.payload.percent_increase)/D(100)
                else:
                    e.amount=None
                e.facts.append(f.fact_id);e.evidence.extend(f.evidence_ids)
                state.changes.append(f'{e.id}: explicit amount amendment {f.fact_id}')
    return state


def infer_streams(state):
    groups = defaultdict(list)
    # A precise semantic selector can separate an affected history from neighbors.
    # Do not globally switch variable-expense history to description grouping.
    precise=[f for f in state.facts if isinstance(f,(AmountAmendment,ScheduleAmendment))
             and f.confirmation_state=='confirmed' and f.stream_selector is not None
             and f.stream_selector.description is not None]
    status_facts = [f for f in state.facts if isinstance(f,StreamStatus) and f.confirmation_state=='confirmed']
    for e in state.events:
        if e.excluded or e.history_excluded or e.status!='settled' or e.event_date>=state.start or not e.settlement or e.settlement>=state.start:
            continue
        statuses = [f.payload.status for f in status_facts if targets(f,e) and applicable(f,state.start)]
        if any(s in ('ended','one_time','contingent') for s in statuses): continue
        if e.direction=='credit' and 'ongoing' not in statuses: continue
        if e.direction=='debit' and e.event_type not in ('expense','subscription','debt_payment'): continue
        if e.amount is None:
            state.issues.append(f'{e.id}: unknown historical amount excluded from center')
            continue
        partition=tuple(f.fact_id for f in precise if targets(f,e))
        groups[(e.category,e.currency,e.flexibility,e.direction,e.event_type,partition)].append(e)
    for key, history in sorted(groups.items()):
        history.sort(key=lambda e:e.event_date)
        if len(history)<3: continue
        dates = [e.event_date for e in history]
        dom, count = Counter(d.day for d in dates).most_common(1)[0]
        eom = all(d.day==calendar.monthrange(d.year,d.month)[1] for d in dates)
        monthly = eom or (count>=3 and D(count)/D(len(dates))>=D('.7'))
        if monthly and not eom: history=[e for e in history if e.event_date.day==dom]
        dates = [e.event_date for e in history]
        # Monthly history must contain consecutive calendar months, not yearly same-day rows.
        month_gaps=[(b.year-a.year)*12+b.month-a.month for a,b in zip(dates,dates[1:])]
        if monthly and D(sum(g==1 for g in month_gaps))/D(len(month_gaps))<D('.7'):
            continue
        gaps = [(b-a).days for a,b in zip(dates,dates[1:])]
        step, matches = Counter(gaps).most_common(1)[0]
        if not monthly and (step not in (5,7,10,14,21) or D(matches)/D(len(gaps))<D('.7')): continue
        amount = history[-1].amount if key[3]=='credit' else sum((e.amount for e in history),ZERO)/D(len(history))
        last = history[-1].settlement if key[3]=='credit' else history[-1].event_date
        if key[3]=='credit' and monthly: dom=last.day
        stream = Stream('stream:'+history[-1].id, history, amount, monthly, step, dom, eom, last)
        stream.amendments=[f for f in state.facts if f.confirmation_state=='confirmed'
                           and isinstance(f,(AmountAmendment,ScheduleAmendment,StreamStatus))
                           and (not isinstance(f,AmountAmendment) or f.stream_selector is not None)
                           and any(targets(f,e) for e in history)]
        state.streams.append(stream)
    return state.streams


def overlap_identity(event, stream, facts):
    anchor = stream.anchor
    if (event.category,event.currency,event.direction)!=(anchor.category,anchor.currency,anchor.direction): return False
    if event.description in {e.description for e in stream.history}: return True
    if event.linked in {e.id for e in stream.history}: return True
    # Semantic membership must name BOTH the explicit event and a history member.
    return any(f.confirmation_state=='confirmed' and event.id in f.affected_event_ids
               and any(e.id in f.affected_event_ids for e in stream.history)
               for f in facts if isinstance(f,(StreamStatus,FutureConfirmation,ScheduleAmendment)))


def fx(amount, currency, home, when, rates):
    if currency==home: return amount
    return amount * rates[(when.isoformat(),currency,home)]


def project(state, rates):
    if state.flows: raise ValueError('State already projected')
    if not state.streams: infer_streams(state)
    for f in state.facts:
        if f.confirmation_state=='confirmed' and isinstance(f,(AmountAmendment,ScheduleAmendment)) and f.stream_selector is not None:
            if not any(f in s.amendments for s in state.streams):
                state.blockers.append(f'{f.fact_id}: amendment stream not established')
            matched=[s for s in state.streams if f in s.amendments]
            if len(matched)>1 or any(any(not targets(f,e) for e in s.history) for s in matched):
                state.blockers.append(f'{f.fact_id}: ambiguous amendment stream membership')
    home=state.profile['home_currency']
    explicit=[]
    for e in state.events:
        if e.excluded: continue
        future = e.settlement and e.settlement>=state.start
        if e.direction=='debit' and e.status in ('pending','scheduled'):
            future=True
        elif e.direction=='credit' and e.status=='scheduled':
            # Only confirmed ongoing income stream membership supports scheduled credit.
            future=bool(future and any(isinstance(f,StreamStatus) and f.payload.status=='ongoing'
                                      and f.confirmation_state=='confirmed' and targets(f,e) and applicable(f,e.settlement) for f in state.facts))
            future=bool(future or (e.settlement and e.settlement>=state.start and any(
                isinstance(f,FutureConfirmation) and f.confirmation_state=='confirmed' and e.id in f.affected_event_ids for f in state.facts)))
        elif e.status!='settled': future=False
        if not future: continue
        if e.settlement and e.settlement>state.end and e.status!='pending': continue
        if e.amount is None or e.settlement is None:
            state.blockers.append(f'{e.id}: unresolved future amount/date'); continue
        # Reserve pending debits immediately; never also debit them at settlement.
        when=state.start if e.status=='pending' else max(state.start,e.settlement)
        explicit.append((e,when))
    for e,when in explicit:
        try: value=fx(e.amount,e.currency,home,e.settlement,rates)
        except KeyError:
            state.blockers.append(f'{e.id}: missing supplied FX');continue
        state.flows.append(Flow(when,value if e.direction=='credit' else -value,e.id,
                                'SEMANTIC_FACT' if e.facts else 'STRUCTURED_EXPLICIT',e.evidence,
                                ['reserve_pending_once'] if e.status=='pending' else [],
                                native_amount=e.amount,currency=e.currency,fx_date=e.settlement))
    for stream in state.streams:
        anchor=stream.anchor
        next_date=add_months(stream.last,dom=stream.dom,eom=stream.eom) if stream.monthly else stream.last+timedelta(days=stream.step)
        while next_date<state.start:
            next_date=add_months(next_date,dom=stream.dom,eom=stream.eom) if stream.monthly else next_date+timedelta(days=stream.step)
        schedule=[f for f in stream.amendments if isinstance(f,ScheduleAmendment) and f.payload.payment_date]
        if any(isinstance(f,ScheduleAmendment) and (f.payload.cadence is not None or f.effective_until is not None or not f.payload.payment_date) for f in stream.amendments):
            state.blockers.append(f'{stream.id}: cadence/ranged/unknown-date amendment outside representative slice');continue
        amount_facts=[f for f in stream.amendments if isinstance(f,AmountAmendment)]
        if len(amount_facts)>1:
            state.blockers.append(f'{stream.id}: conflicting amount amendments require source precedence');continue
        # Conflicting dates without reliable source precedence remain explicit blockers.
        if len({f.payload.payment_date for f in schedule})>1:
            state.blockers.append(f'{stream.id}: conflicting schedule facts');continue
        amendment=schedule[-1] if schedule else None
        first_amended=day(amendment.payload.payment_date) if amendment else None
        dom=stream.dom
        if amendment:
            if first_amended>=state.start: next_date=first_amended
            if amendment.payload.scope!='one_cycle':
                dom=first_amended.day
                if first_amended<state.start:
                    next_date=first_amended
                    while next_date<state.start: next_date=add_months(next_date,dom=dom)
        index=0
        while next_date<=state.end:
            when=next_date
            policies=['observed_cadence','historical_mean' if anchor.direction=='debit' else 'last_contractual_pay']
            evidence=[e.id for e in stream.history]
            provenance='INFERRED_RECURRENCE'
            if amendment:
                evidence+=amendment.evidence_ids
                provenance='SEMANTIC_FACT' if when==first_amended else 'MODELING_POLICY'
                if when!=first_amended: policies.append('persist_payday_phase' if amendment.payload.scope!='one_cycle' else 'return_to_historical_phase')
            active_status=[f for f in stream.amendments if isinstance(f,StreamStatus) and applicable(f,when)]
            excluded=any(f.payload.status in ('ended','one_time','contingent') for f in active_status)
            amount=stream.amount
            for f in [f for f in stream.amendments if isinstance(f,AmountAmendment) and applicable(f,when)]:
                if f.payload.scope=='one_cycle' and index>0: continue
                if f.payload.money and f.payload.money.currency!=anchor.currency:
                    state.blockers.append(f'{f.fact_id}: currency mismatch');excluded=True;continue
                if f.payload.money and f.payload.money.value is not None:
                    amount=decimal(f.payload.money.value)
                elif f.payload.percent_increase is not None:
                    amount=stream.amount*(D(1)+decimal(f.payload.percent_increase)/D(100))
                else:
                    state.blockers.append(f'{f.fact_id}: unknown amended amount');excluded=True;continue
                evidence+=f.evidence_ids;policies.append('apply_evidence_amendment')
                if f.payload.scope=='unknown': policies.append('persist_amount_amendment_unknown_duration')
            overlaps=[e for e,_ in explicit if overlap_identity(e,stream,state.facts)
                      and (e.settlement==when or (e.linked in {h.id for h in stream.history}
                           and stream.monthly and (e.settlement.year,e.settlement.month)==(when.year,when.month)))]
            if overlaps:
                state.changes.append(f'{stream.id}@{when}: explicit {overlaps[0].id} replaces inferred occurrence')
            elif not excluded:
                try: value=fx(amount,anchor.currency,home,when,rates)
                except KeyError: state.blockers.append(f'{stream.id}@{when}: missing supplied FX');value=None
                if value is not None:
                    state.flows.append(Flow(when,value if anchor.direction=='credit' else -value,stream.id,provenance,
                                            evidence,policies,stream.id,amount,anchor.currency,when))
            index+=1
            next_date=add_months(when,dom=dom,eom=stream.eom) if stream.monthly else when+timedelta(days=stream.step)
    for e,_ in explicit:
        for s in state.streams:
            if e.category==s.anchor.category and e.direction==s.anchor.direction and not overlap_identity(e,s,state.facts):
                state.issues.append(f'{e.id}/{s.id}: overlap unestablished; both retained')
    # Facts confirming genuinely new future occurrences, not amounts inferred by a model.
    for f in state.facts:
        if not isinstance(f,FutureConfirmation) or f.confirmation_state!='confirmed':continue
        if f.affected_event_ids:
            continue
        # A new semantic-only confirmation is not an instruction to add a second
        # obligation. This slice cannot establish overlap without an event identity.
        if any(targets(f,s.anchor) for s in state.streams):
            state.blockers.append(f'{f.fact_id}: new confirmation overlaps a stream without event identity');continue
        payload=f.payload
        if payload.money.value is None or payload.payment_date is None:
            state.blockers.append(f'{f.fact_id}: future confirmation incomplete');continue
        when=day(payload.payment_date)
        if state.start<=when<=state.end:
            try: value=fx(decimal(payload.money.value),payload.money.currency,home,when,rates)
            except KeyError: state.blockers.append(f'{f.fact_id}: missing supplied FX');continue
            state.flows.append(Flow(when,value if payload.direction=='credit' else -value,f.fact_id,'SEMANTIC_FACT',f.evidence_ids,[]))
    state.flows.sort(key=lambda f:(f.when,f.amount>=0,f.source))
    return state


def daily_path(state, flows=None, payments=()):
    """Policy: reserve/expense debits, then confirmed credits, then purchase payments.

    Intraday essential-debit troughs are checked, not just net daily balances.
    Purchase payments can use that day's settled income.
    """
    groups=defaultdict(list)
    for f in state.flows if flows is None else flows: groups[f.when].append(f.amount)
    pays=defaultdict(Decimal)
    for when,amount in payments: pays[when]+=amount
    balance=decimal(state.profile['current_available_balance'])
    rows=[]
    for i in range(90):
        when=state.start+timedelta(days=i)
        amounts=groups[when]
        before=balance
        balance+=sum((v for v in amounts if v<0),ZERO)
        expense_min=balance
        balance+=sum((v for v in amounts if v>0),ZERO)
        balance-=pays[when]
        rows.append(dict(date=when,balance=balance,minimum=min(before,expense_min,balance)))
    return rows


def capacity(state):
    if state.blockers: raise ValueError('Unresolved financial state: '+'; '.join(state.blockers))
    floor=decimal(state.profile['minimum_balance_to_keep'])
    requested=decimal(state.request['requested_amount'])
    path=daily_path(state)
    minimum=min(decimal(state.profile['current_available_balance']),*(r['minimum'] for r in path))
    # Today's payment follows known same-day cash; later expense minima constrain it.
    today_capacity=min(path[0]['balance'],*(r['minimum'] for r in path[1:]))-floor
    safe=max(ZERO,min(requested,today_capacity)).quantize(CENT,rounding=ROUND_DOWN)
    if minimum<floor: safe=ZERO
    earliest=None
    for i,row in enumerate(path):
        prefix=min((r['minimum'] for r in path[:i+1]),default=minimum)
        suffix=min([row['balance']]+[r['minimum'] for r in path[i+1:]])
        if prefix>=floor and suffix-requested>=floor:
            earliest=row['date'];break
    return safe,earliest,minimum,path
