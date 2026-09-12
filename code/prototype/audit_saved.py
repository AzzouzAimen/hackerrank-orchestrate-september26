"""Offline assistant adjudications for the three frozen September 12 artifacts.

These case-specific judgments are evaluation annotations, not an inference rulebook.
Human approval is pending. Unknown source hashes fail closed. No model calls.
"""
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from .extraction_experiment import ARTIFACTS, ROOT, build_cases, score, rows

OUT = ARTIFACTS / 'audit_v2'
VERSION = 'assistant-evidence-audit-v2.0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(name, value):
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    path = OUT / name
    if path.exists():
        if path.read_text(encoding='utf-8') != text:
            raise ValueError('Existing audit differs; use a new version: ' + name)
        return
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def review(case_id, f):
    """Compact, manually authored fact-level decisions with separate dimensions."""
    typ, p = f['fact_type'], f['payload']
    d = dict(judgment='supported', target='correct', value_fidelity='correct',
             uncertainty_fidelity='preserved', failure_category=None,
             ownership='none', rationale='', role='supported_extra',
             effective_bounds='not asserted' if not (f['effective_from'] or f['effective_until'])
                              else 'supported occurrence/observed-range bound; not proof of stream inception')
    if case_id == 'rep_user01':
        if typ == 'lifecycle_relationship':
            d['role'] = 'critical'
            if p['relationship'] == 'refund_of':
                d['rationale'] = 'event_99 explicitly describes a settled reversal linked to event_98; event date is supplied, not invented.'
            else:
                assert p['relationship'] == 'retry_of'
                d.update(judgment='incorrect', value_fidelity='incorrect relationship',
                         failure_category='LIFECYCLE_MISINTERPRETATION', ownership='model',
                         rationale='event_101 is a settled card purchase linked to cancelled authorization event_100. No failed purchase/retry is stated; settlement_of is supported.')
            if p['related_event_id'] in f['affected_event_ids']:
                d.update(judgment='incorrect', target='incorrect: parent also asserted as child')
                d['failure_category'] = (d['failure_category'] + '|WRONG_TARGET' if d['failure_category'] else 'WRONG_TARGET')
                d['ownership'] = 'model'
                d['rationale'] += ' Parent in affected_event_ids asserts a self-relationship; provenance may list both legs, but the child target should not.'
        elif typ == 'cash_classification':
            assert p['classification'] == 'historical_only'
            d.update(judgment='redundant', role='supported_restatement',
                     rationale='Cancelled authorization is not available cash. historical_only restates the supplied cancelled state; no current cash is fabricated.')
        elif typ == 'future_event_confirmation':
            assert p['money']['value'] == '23320'
            d['rationale'] = 'event_103 explicitly supplies Next confirmed salary, ZAR 23320 and 2024-03-15. Supported extra even though the reference chose ongoing stream status.'
        else:
            raise AssertionError(f)
    elif case_id in {'rep_user07', 'rep_user16', 'rep_user21', 'rep_user25'}:
        if typ == 'stream_status':
            d['role'] = 'critical'
            d['rationale'] = 'Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary.'
            if f['confirmation_state'] == 'uncertain':
                d.update(judgment='ambiguous', uncertainty_fidelity='conservative, differs from reference',
                         failure_category='EVALUATION_AMBIGUITY', ownership='reference/prompt semantics',
                         rationale=d['rationale'] + ' Future permanence is not guaranteed. Reference confirmed versus model uncertain changes resolver eligibility; neither certainty convention is independently approved.')
        elif case_id == 'rep_user07' and typ == 'date_or_schedule_amendment':
            d['role'] = 'critical'
            d['rationale'] = 'message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit.'
            if p['scope'] == 'one_cycle':
                d.update(judgment='unsupported', uncertainty_fidelity='duration asserted beyond evidence',
                         failure_category='UNCERTAINTY_TO_CERTAINTY', ownership='model')
                d['rationale'] += ' The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved.'
            if f['effective_from']:
                d['effective_bounds'] = 'EVALUATION_AMBIGUITY: payment date is evidenced, but when the amendment starts applying is not stated'
                d['rationale'] += ' effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved.'
        elif case_id == 'rep_user07' and typ == 'future_event_confirmation':
            d['rationale'] = 'message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history.'
            if p['money']['value'] is not None:
                assert p['money']['value'] == '149000'
                d.update(judgment='unsupported', value_fidelity='historical value incorrectly confirmed for future payment',
                         uncertainty_fidelity='unknown future amount became certain',
                         failure_category='UNCERTAINTY_TO_CERTAINTY', ownership='model')
                d['rationale'] += ' INR 149000 is historically supported, not a confirmed future amount. Python may project it; extraction may not assert confirmation.'
        elif typ == 'cash_classification':
            if p['classification'] == 'cash':
                d.update(judgment='redundant', role='supported_restatement',
                         rationale='The targeted salary rows are settled cash; bounds bracket exactly the supplied historical settlements.')
            else:
                assert p['classification'] == 'pending_credit'
                d.update(judgment='incorrect', value_fidelity='scheduled/confirmed salary misclassified as pending_credit',
                         failure_category='CASH_STATE_MISINTERPRETATION', ownership='model/field semantics',
                         rationale='Evidence confirms future salary, not a pending bank credit. pending_credit is a resolver exclusion, so ordinary-language not-yet-paid is not equivalent to this cash classification.')
        elif case_id == 'rep_user16' and typ == 'amount_amendment':
            assert p['percent_increase'] == '12'
            d.update(judgment='ambiguous', role='critical',
                     target='ambiguous: outstanding balance is not established as renewed lease stream',
                     uncertainty_fidelity='scope unknown is conservative; renewed lease suggests ongoing',
                     failure_category='EVALUATION_AMBIGUITY', ownership='input/reference and model targeting',
                     rationale='message_12 states a 12% renewed monthly lease increase. Input omits every Monthly rent event, while the reference demands that exact selector. Linking it to event_1442 is not established; cannot attribute the target failure solely to the model.')
        elif case_id == 'rep_user16' and typ == 'image_financial_value':
            if p['value_type'] == 'current_amount_due':
                d.update(judgment='incorrect', value_fidelity='gross total is not remaining balance',
                         failure_category='IMAGE_MISINTERPRETATION', ownership='model',
                         rationale='image_02 shows total 200000, received 100000, Balance Due 100000. The gross total is not the current amount due; numeric OCR itself is correct.')
            elif p['value_type'] == 'amount_paid':
                d.update(target='correct image link; historical payment is not scheduled debit',
                         rationale='Amount Received INR 100000 is visibly supported. This is a supported extra receipt field, not a license to overwrite future outstanding debt; the engine already rejects that use.')
            else:
                assert p['value_type'] == 'balance_due'
                d.update(role='critical', rationale='Balance Due INR 100000 is visible in image_02 and image metadata links event_1442. Historical receipt period does not amend the supplied scheduled settlement date.')
        elif typ == 'future_event_confirmation':
            d['rationale'] = 'Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference.'
            if case_id == 'rep_user16':
                d.update(judgment='ambiguous', uncertainty_fidelity='unknown relative to row, known from supplied image',
                         failure_category='EVALUATION_AMBIGUITY', ownership='decomposition/resolver compatibility',
                         rationale=d['rationale'] + ' Same bundle also extracts Balance Due. Separate row-null and image-value claims have supported provenance but are not equivalent consolidated resolver inputs.')
        elif typ in {'amount_amendment', 'date_or_schedule_amendment'}:
            d.update(judgment='ambiguous', value_fidelity='observed values/cadence supported; amendment not established',
                     uncertainty_fidelity='ongoing fixed amount/cadence exceeds explicit confirmation',
                     failure_category='EVALUATION_AMBIGUITY', ownership='prompt/field semantics',
                     rationale='Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent.')
        else:
            raise AssertionError(f)
    elif case_id == 'unused_real_image03':
        assert typ == 'image_financial_value'
        if p['value_type'] == 'amount_paid':
            d.update(role='critical', rationale='Direct visual audit: Cash Paid 41272.00, same numeric value as 41272. Event supplies INR and 2026-02-27; receipt date agrees. effective_from is not fabricated.')
        else:
            assert p['value_type'] == 'current_amount_due'
            d.update(judgment='incorrect', value_fidelity='paid gross amount misinterpreted as outstanding',
                     failure_category='IMAGE_MISINTERPRETATION', ownership='model',
                     rationale='Net Amount 41272.0 equals Cash Paid 41272.00 on the receipt and the linked event is settled. It does not establish a current amount due. Numeric OCR and currency are correct.')
    elif case_id == 'synthetic_unknown_obligation':
        if typ == 'future_event_confirmation':
            d.update(role='critical', rationale='syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event.')
        else:
            assert typ in {'amount_amendment', 'date_or_schedule_amendment'}
            d.update(judgment='redundant', role='supported_restatement',
                     rationale='Restates the same unknown amount or date already present in future confirmation. No value or duration invented. Equivalent financial meaning; extra amendment objects are not promised to be resolver-equivalent.')
    elif case_id == 'synthetic_possible_duplicate':
        assert p['relationship'] == 'possible_duplicate_of'
        d.update(role='critical', rationale='syn_msg_duplicate explicitly says b might duplicate a, investigation open. Correct child/parent, possible relation and uncertain confirmation are preserved.')
    elif case_id == 'synthetic_conflict_two_streams':
        d.update(judgment='ambiguous', role='critical', target='correct Dinner identity; event-restricted scope needs adjudication',
                 failure_category='EVALUATION_AMBIGUITY', ownership='target semantics/evaluation',
                 rationale='Newer same-source correction supports USD 25 for next month only; Lunch is unchanged. Both target the Dinner identity. Explicit syn_dinner ID restricts the selector to history, it does not broaden it. It may denote stream membership, but equivalence to an open future selector is not established; do not score it automatically correct or hallucinated.')
    else:
        raise AssertionError(f)
    d['reviewer_provenance'] = 'assistant audit; pending human review'
    return d


def reference_review(case_id, ref, run, fact_reviews):
    typ = ref['fact_type']
    if not run['usable']:
        return 'output_unavailable', 'No usable bundle; excluded from conditional semantic misses.'
    if case_id == 'rep_user01':
        if typ == 'stream_status':
            if ref['payload']['status'] == 'ongoing':
                return 'reference_ambiguous', 'One prorated payment and one confirmed future salary do not establish an ongoing stream; future confirmation is supported instead.'
            return 'missed', 'Prorated first salary is a supported special one-time amount; no equivalent classification was emitted.'
        if ref['payload']['relationship'] == 'settlement_of':
            return 'incorrect', 'Model emits retry_of; not the supported authorization settlement meaning.'
        child = next(f for f in run['bundle']['facts'] if f['payload'].get('relationship') == 'refund_of')
        return ('partial' if len(child['affected_event_ids']) > 1 else 'recovered'), 'Refund relationship recovered; inspect child target separately.'
    if case_id == 'rep_user07':
        if typ == 'stream_status':
            f = next(f for f in run['bundle']['facts'] if f['fact_type'] == typ)
            return ('partial' if f['confirmation_state'] == 'uncertain' else 'recovered'), 'Ongoing history recognized; uncertain confirmation differs materially from reference, whose certainty convention needs approval.'
        f = next(f for f in run['bundle']['facts'] if f['fact_type'] == typ)
        return ('partial' if f['payload']['scope'] == 'one_cycle' else 'recovered'), 'Correct confirmed next date and stream; one_cycle is unsupported when emitted. Payment-date applicability bound remains a separate ambiguity.'
    if case_id == 'rep_user16' and typ == 'amount_amendment':
        return 'input_limited', '12 percent recovered, but Monthly rent history needed for reference target was omitted; do not claim a counterfactual answer.'
    if case_id == 'synthetic_conflict_two_streams':
        return 'partial', 'Amount, currency, one-cycle duration and Dinner identity recovered; explicit historical target versus open stream scope unresolved.'
    return 'recovered', 'Supported critical meaning recovered; see fact-level dimensions and source evidence.'


def main():
    before = json.loads((OUT / 'before_hashes.json').read_text(encoding='utf-8'))
    cases = {c['case_id']: c for c in build_cases()}
    # Reconstructed input snapshot, never described as a saved original request body.
    snapshot = {k: {"evidence": c['evidence'], "reference": c['reference'],
                    "images": [{"path": str(Path(p).relative_to(ROOT)).replace('\\', '/'),
                                "sha256": sha(Path(p))} for p in c['image_paths']]}
                for k, c in cases.items()}
    emit('evidence_snapshot.json', {'provenance': 'Reconstructed from current frozen case builder; original full request bodies were not saved.',
                                  'cases': snapshot})
    all_reviews, references, operational, comparisons = [], [], [], []
    for source in sorted(ARTIFACTS.glob('experiment_*.json')):
        key = 'prototype/extraction_artifacts/' + source.name
        assert sha(source) == before[key], 'Source changed since pre-audit manifest'
        a = json.loads(source.read_text(encoding='utf-8'))
        runs = a['records'] + a['repeats']
        for r in runs:
            identity = {'source_artifact': source.name, 'source_sha256': sha(source),
                        'case_id': r['case_id'], 'run_index': r.get('repeat_index', 1)}
            run = r['run']; c = cases[r['case_id']]
            reviewed = []
            for i, f in enumerate((run['bundle'] or {}).get('facts', [])):
                reviewed.append({**identity, 'fact_index': i, 'fact_id': f['fact_id'],
                                 'fact': f, 'relevant_evidence': f['evidence_ids'],
                                 **review(r['case_id'], f)})
            all_reviews.extend(reviewed)
            comparisons.append({**identity, 'automatic_reference_comparison': score(c, run)})
            for ref in c['reference']['facts']:
                status, rationale = reference_review(r['case_id'], ref, run, reviewed)
                references.append({**identity, 'reference_id': ref['fact_id'], 'status': status,
                                   'rationale': rationale, 'reviewer_provenance': 'assistant audit; pending human review'})
        attempts = [t for r in runs for t in r['run']['attempts']]
        latency = [t['latency_seconds'] for t in attempts if t.get('latency_seconds') is not None]
        prompt = sum(t.get('usage', {}).get('prompt_tokens', 0) or 0 for t in attempts)
        cached = sum(t.get('usage', {}).get('cached_tokens', 0) or 0 for t in attempts)
        completion = sum(t.get('usage', {}).get('completion_tokens', 0) or 0 for t in attempts)
        operational.append({'source': source.name, 'sha256': sha(source), 'logical_runs': len(runs),
            'baseline_usable': sum(r['run']['usable'] for r in a['records']),
            'baseline_first_valid': sum(r['run']['attempts'][0]['schema_valid'] for r in a['records']),
            'all_usable': sum(r['run']['usable'] for r in runs),
            'all_first_valid': sum(r['run']['attempts'][0]['schema_valid'] for r in runs),
            'calls': len(attempts), 'retries': sum(len(r['run']['attempts']) - 1 for r in runs),
            'provider_failures': sum(bool(t.get('provider_failure')) for t in attempts),
            'empty_successful_responses': sum(not t.get('provider_failure') and t.get('raw_content') == '' for t in attempts),
            'prompt_tokens': prompt, 'cached_tokens': cached, 'completion_tokens': completion,
            'total_tokens': prompt + completion,
            'estimated_cost_usd': ((prompt-cached)*0.15+cached*0.03+completion*0.5)/1000000,
            'latency_mean': statistics.mean(latency) if latency else None,
            'latency_median': statistics.median(latency) if latency else None,
            'recorded_evaluation_revision': a.get('evaluation_revision'),
            'errors': [{'case_id': r['case_id'], 'run_index': r.get('repeat_index', 1),
                        'attempt': t['attempt'], 'category': 'PROVIDER_API_FAILURE' if t.get('provider_failure') else 'EMPTY_OUTPUT' if t.get('raw_content') == '' else 'MALFORMED_OUTPUT'}
                       for r in runs for t in r['run']['attempts'] if not t['schema_valid']]})
    emit('claim_review.json', {'evaluator_version': VERSION, 'reviewer': 'Codex assistant; no documented independent human approval',
         'scope': 'Every emitted fact in all baselines and selected repeats in all three timestamped artifacts.',
         'claims': all_reviews})
    emit('reference_review.json', {'evaluator_version': VERSION, 'units': 'Original reference slots, with defects and partial meanings explicit; not unquestionable ground truth.', 'references': references})
    emit('automatic_comparisons.json', {'records': comparisons})
    emit('operations.json', {'runs': operational, 'billing_limit': 'Recorded attempts only; smoke/diagnostic usage may be missing. Not session billing.'})
    rent = [e for e in rows('financial_events') if e['user_id'] == 'user_16' and e['description'] == 'Monthly rent']
    emit('proposed_input_addition.json', {'case_id': 'rep_user16', 'variable': 'append omitted Monthly rent history only',
         'new_events': rent, 'executed': False, 'reason': 'Existing supplied outstanding balance is a separate event; preserve all original inputs and references for a paired comparison.'})
    for op in operational:
        source = op['source']; base = [r for r in all_reviews if r['source_artifact'] == source and r['run_index'] == 1]
        refs = [r for r in references if r['source_artifact'] == source and r['run_index'] == 1]
        print(source, 'baseline judgments', dict(Counter(r['judgment'] for r in base)),
              'reference meanings', dict(Counter(r['status'] for r in refs)))


if __name__ == '__main__':
    main()
