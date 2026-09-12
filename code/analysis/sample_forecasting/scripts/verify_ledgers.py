"""Three-case audit of existing behavior, not a new forecasting engine.

Case IDs select audit inputs only. Labels never enter simulate(). Decimal replay
checks the emitted, already rounded research cash flows; it does not convert the
float-based simulator into production Decimal arithmetic.
"""
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal
import csv
import json
import investigate as sim

OUT = sim.OUT / 'ledger_verification'
CASES = ('user_07', 'user_21', 'user_12')
INPUT_FIELDS = ('request_id', 'user_id', 'request_date', 'request_type',
                'requested_amount', 'desired_completion_date',
                'allows_partial_payment', 'request_text')


def money(value):
    return Decimal(str(value))


def forecast(request, **kwargs):
    return sim.simulate({key: request[key] for key in INPUT_FIELDS}, **kwargs)


def ledger(request, result):
    events = {e['event_id']: e for e in sim.EVENTS if e['user_id'] == request['user_id']}
    streams = {s['category']: s for s in result['streams']}
    messages = [m for m in sim.MESSAGES if m['user_id'] == request['user_id']
                and m['sent_at'][:10] <= request['request_date']]
    balance = money(sim.PROFILES[request['user_id']]['current_available_balance'])
    rows = [dict(date=request['request_date'], source_event='opening profile snapshot',
                 direction='opening', amount=str(balance), running_balance=str(balance),
                 provenance='MODELING_POLICY', evidence_ids=request['user_id'],
                 policy='Profile treated as opening balance; historical cash not replayed.')]
    for date, signed, source in result['trace']:
        provenance = 'STRUCTURED_EXPLICIT'
        evidence = source
        policy = 'Cash on settlement date; pending debit charged once in this trace.'
        if source.startswith('recurring:'):
            stream = streams[source.split(':', 1)[1]]
            evidence = stream['anchor']
            provenance = 'INFERRED_RECURRENCE'
            policy = f"Observed cadence {stream['cadence']}; historical mean for variable amounts."
            anchor = events[stream['anchor']]
            if anchor['status'] == 'scheduled' and anchor['settlement_date'] == date:
                provenance = 'STRUCTURED_EXPLICIT'
                policy = 'Scheduled salary emitted via salary loop, once; source is explicit.'
            if stream['category'] == 'salary':
                for message in messages:
                    if 'replaces the payroll date' in message['message_text'].lower():
                        evidence += '|' + message['message_id']
                        if date in message['message_text']:
                            provenance = 'SEMANTIC_FACT'
                            policy = 'Message supplies this payday; amount comes from payroll history.'
                        else:
                            provenance = 'MODELING_POLICY'
                            policy = 'UNRESOLVED: persist revised payday into later months; duration not stated.'
        balance += money(signed)
        rows.append(dict(date=date, source_event=source,
                         direction='credit' if signed > 0 else 'debit',
                         amount=str(abs(money(signed))), running_balance=str(balance),
                         provenance=provenance, evidence_ids=evidence, policy=policy))
    return rows


def replay(request, result):
    """Independent end-of-day capacity calculation from the emitted trace."""
    profile = sim.PROFILES[request['user_id']]
    opening = money(profile['current_available_balance'])
    floor = money(profile['minimum_balance_to_keep'])
    requested = money(request['requested_amount'])
    flows = defaultdict(Decimal)
    for date, signed, _ in result['trace']:
        flows[date] += money(signed)
    balance = opening
    path = []
    start = sim.day(request['request_date'])
    for offset in range(90):
        date = (start + timedelta(days=offset)).isoformat()
        balance += flows[date]
        path.append((date, balance))
    baseline = min(opening, *(b for _, b in path))
    safe = max(Decimal(0), min(requested, baseline - floor))
    earliest = next((d for i, (d, _) in enumerate(path)
                     if min(b for _, b in path[i:]) >= floor + requested), '')
    return baseline, safe, earliest, path


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table(rows, fields):
    return '\n'.join(['| ' + ' | '.join(fields) + ' |',
                      '| ' + ' | '.join('---' for _ in fields) + ' |'] +
                     ['| ' + ' | '.join(str(row.get(f, '')).replace('|', ', ') for f in fields) + ' |'
                      for row in rows])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    comparisons, bundles = [], {}
    for user in CASES:
        request = next(r for r in sim.SAMPLES if r['user_id'] == user)
        result = forecast(request)
        rows = ledger(request, result)
        baseline, safe, earliest, path = replay(request, result)
        assert baseline.quantize(Decimal('.01')) == money(result['min_balance'])
        assert safe.quantize(Decimal('.01')) == money(result['safe'])
        assert earliest == result['earliest']
        profile = sim.PROFILES[user]
        comparison = dict(user=user, currency=profile['home_currency'],
                          opening=profile['current_available_balance'],
                          floor=profile['minimum_balance_to_keep'],
                          request_date=request['request_date'],
                          endpoint=(sim.day(request['request_date']) + timedelta(days=89)).isoformat(),
                          binding_date=result['min_date'], minimum=result['min_balance'],
                          predicted_safe=result['safe'], labeled_safe=request['amount_safe_to_pay'],
                          predicted_earliest=earliest, labeled_earliest=request['earliest_date_for_full_payment'])
        comparisons.append(comparison)
        events = [e for e in sim.EVENTS if e['user_id'] == user]
        messages = [m for m in sim.MESSAGES if m['user_id'] == user]
        bundles[user] = dict(comparison=comparison, streams=result['streams'],
                             future_explicit_events=[e for e in events if e['settlement_date'] >= request['request_date']],
                             excluded_nonsettled=[e for e in events if e['status'] in ('unrealized','failed','cancelled','pending')],
                             messages=messages, ledger=rows,
                             variants={name: {k: v for k, v in forecast(request, **kw).items()
                                              if k in ('safe','earliest','min_balance','min_date')}
                                       for name, kw in [('one_cycle', dict(delay_persists=False)),
                                                        ('reserve_pending_now', dict(hold_today=True)),
                                                        ('calendar_endpoint', dict(monthly_horizon=True))]})
        components = defaultdict(Decimal)
        for row in rows[1:]:
            if row['date'] <= result['min_date']:
                components[row['source_event']] += money(row['amount']) * (1 if row['direction'] == 'credit' else -1)
        bundles[user]['binding_components'] = {k: str(v) for k,v in components.items()}
        bundles[user]['safe_error'] = str(money(result['safe']) - money(request['amount_safe_to_pay']))
        bundles[user]['label_implied_minimum_or_lower_bound'] = str(money(profile['minimum_balance_to_keep']) + money(request['amount_safe_to_pay']))
        write_csv(OUT / f'{user}_ledger.csv', rows)
        write_csv(OUT / f'{user}_daily.csv', [dict(date=d, balance=str(b)) for d, b in path])
    write_csv(OUT / 'comparison.csv', comparisons)
    request = next(r for r in sim.SAMPLES if r['user_id'] == 'user_12')
    calendar = forecast(request, monthly_horizon=True)
    literal = forecast(request)
    boundary = list((Counter(literal['trace']) - Counter(calendar['trace'])).elements())
    bundles['user_12']['literal_only_events'] = boundary
    request = next(r for r in sim.SAMPLES if r['user_id'] == 'user_21')
    # Audit the supplied actions, never use these label actions in baseline inference.
    changes = {}
    event_map = {e['event_id']: e for e in sim.EVENTS}
    actions = []
    for action in request['spending_changes_needed'].split('|'):
        kind, event_id, *value = action.split(':')
        event = event_map[event_id]
        amount = money(value[0]) if value else Decimal(0)
        profile = sim.PROFILES[request['user_id']]
        permission = event['category'] in profile['expense_categories_user_is_willing_to_' + ('stop' if kind == 'stop' else 'reduce')].split('|')
        permission &= event['category'] not in profile['expense_categories_to_protect'].split('|')
        permission &= event['flexibility'] in (('stoppable','reducible_or_stoppable') if kind == 'stop' else ('reducible','reducible_or_stoppable'))
        if kind != 'stop':
            permission &= bool(event['minimum_allowed_amount']) and amount >= money(event['minimum_allowed_amount'])
            permission &= amount <= money(event['amount'])
        assert permission
        changes[event['category']] = float(amount)
        actions.append(dict(action=action, permission_valid=bool(permission), minimum_allowed=event['minimum_allowed_amount']))
    changed = forecast(request, changes=changes)
    bundles['user_21']['labeled_actions_audit'] = actions
    bundles['user_21']['after_labeled_actions'] = {k: changed[k] for k in ('min_balance','safe','earliest')}
    requested = money(request['requested_amount'])
    bundles['user_21']['full_payment_minimum_without_changes'] = str(money(forecast(request)['min_balance']) - requested)
    bundles['user_21']['full_payment_minimum_with_changes'] = str(money(changed['min_balance']) - requested)
    (OUT / 'audit.json').write_text(json.dumps(bundles, indent=2), encoding='utf-8')
    report = ['# Three-case ledger verification', '',
              'Research audit only. Historical gate: STOP — unresolved modeling assumption about future payroll phase. '
              'No evidence contradiction establishes a different horizon or estimator. '
              'The user subsequently accepted a documented Python persistence policy; see LEDGER_GATE.md for current status.', '',
              table(comparisons, ['user','currency','predicted_safe','labeled_safe','predicted_earliest','labeled_earliest']), '',
              'Each CSV contains date, source/event, debit/credit, amount, running balance, provenance and evidence IDs. '
              'Opening snapshot treatment and later amended payroll phases are labeled MODELING_POLICY. '
              'A scheduled salary emitted by the old recurrence loop is correctly attributed to STRUCTURED_EXPLICIT. '
              'Row ordering reproduces the existing sorted trace (debits before credits on a shared date); '
              'the simulator itself tests daily net balances, not intraday ordering. '
              'Decimal replay validates those emitted cent-rounded flows, not production money precision.', '']
    for user, bundle in bundles.items():
        report += [f'## {user}', '', table([bundle['comparison']],
                   ['opening','floor','request_date','endpoint','binding_date','minimum']), '',
                   'Inferred streams (anchor is a historical evidence ID, not a new future event):', '',
                   table(bundle['streams'], ['category','anchor','n','cadence','amount','first']), '',
                   'Future explicit events:', '',
                   table(bundle['future_explicit_events'], ['event_id','description','status','settlement_date','amount']) if bundle['future_explicit_events'] else 'None.', '',
                   'Semantic source evidence:', '']
        report += [f"- {m['message_id']}: {m['message_text']}" for m in bundle['messages']] or ['None.']
        report += ['', f"[Complete ledger](../artifacts/ledger_verification/{user}_ledger.csv) and "
                   f"[90 daily balances](../artifacts/ledger_verification/{user}_daily.csv).", '',
                   table(bundle['ledger'], ['date','source_event','direction','amount','running_balance','provenance']), '']
    report += ['## Diagnostic results', '',
               'Existing diagnostics only; none selected to improve labels.', '',
               table([dict(user=u, diagnostic=n, **v) for u, b in bundles.items() for n, v in b['variants'].items()],
                     ['user','diagnostic','min_balance','safe','earliest']), '',
               'Literal-only boundary cash flows for user_12:', '',
               table([dict(date=d, signed_amount=a, source=s) for d,a,s in boundary], ['date','signed_amount','source']), '',
               'user_21 supplied spending actions (audit only):', '',
               table(actions, ['action','permission_valid','minimum_allowed']), '',
               'Full payment minimum without changes: ' + bundles['user_21']['full_payment_minimum_without_changes'] +
               '; with supplied changes: ' + bundles['user_21']['full_payment_minimum_with_changes'] + '.', '',
               'See [interpretation and verification gate](LEDGER_GATE.md) for classifications and next step.', '']
    (sim.OUT.parent / 'reports' / 'LEDGER_VERIFICATION.md').write_text('\n'.join(report), encoding='utf-8')
    print(table(comparisons, ['user','minimum','predicted_safe','labeled_safe','predicted_earliest','labeled_earliest']))
    print(json.dumps({u: b['variants'] for u,b in bundles.items()}, indent=2))
    print(json.dumps({u: {k: b[k] for k in ('binding_components','safe_error','label_implied_minimum_or_lower_bound')} for u,b in bundles.items()}, indent=2))
    print(json.dumps({k: bundles['user_21'][k] for k in ('labeled_actions_audit','after_labeled_actions','full_payment_minimum_without_changes','full_payment_minimum_with_changes')}, indent=2))


if __name__ == '__main__':
    main()
