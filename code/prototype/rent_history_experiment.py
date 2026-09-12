"""Capped shadow experiment. Preparation is offline; inference requires --run."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import extraction_experiment as frozen

VERSION = 'rent-history-v1'
RENT_IDS = ['event_1337', 'event_1344', 'event_1351', 'event_1358', 'event_1365', 'event_1371']
RUBRIC = {
    'version': VERSION,
    'lease_target': 'Renewed Monthly rent stream; do not apply 12% to event_1442.',
    'control_abstention': 'Abstention is distinct from incorrect targeting, not a semantic error.',
    'scope': 'Accept ongoing or unknown for primary targeting; report scope separately. No invented bounds or one-cycle limitation.',
    'image': 'Balance Due INR 100000 links to event_1442; preserve structured settlement date. Gross total and paid amount are not current debt.',
    'review': 'Human-approved conventions do not make assistant claim judgments human ground truth.',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def arms():
    control = next(c for c in frozen.build_cases() if c['case_id'] == 'rep_user16')
    addition = json.loads((frozen.ARTIFACTS / 'audit_v2/proposed_input_addition.json').read_text())['new_events']
    actual = [e for e in frozen.rows('financial_events') if e['event_id'] in RENT_IDS]
    if addition != actual or [e['event_id'] for e in addition] != RENT_IDS:
        raise ValueError('Proposed rent rows differ from the reviewed dataset rows')
    if any(e['event_id'] in RENT_IDS for e in control['evidence']['events']):
        raise ValueError('Control already contains treatment history')
    treatment = copy.deepcopy(control)
    treatment['evidence']['events'].extend(addition)
    return {'control': control, 'treatment': treatment}


def payload(case, correction=None):
    # This is the exact body construction used by the frozen call_model.
    return {'model': frozen.MODEL, 'messages': [
        {'role': 'system', 'content': frozen.SYSTEM_PROMPT},
        {'role': 'user', 'content': frozen.request_content(case, correction)}], **frozen.SETTINGS}


def prepare():
    cases = arms()
    return {
        'version': VERSION, 'executed': False, 'rubric': RUBRIC,
        'rubric_sha256': digest(RUBRIC),
        'configuration': {'provider': frozen.PROVIDER, 'endpoint': frozen.ENDPOINT,
                          'integration_version': frozen.INTEGRATION_VERSION,
                          'timeout_seconds': frozen.REQUEST_TIMEOUT_SECONDS,
                          'model': frozen.MODEL, 'settings': frozen.SETTINGS,
                          'prompt_version': frozen.PROMPT_VERSION,
                          'system_prompt': frozen.SYSTEM_PROMPT,
                          'schema': frozen.compact_schema(),
                          'retry_policy': 'one visible retry after provider or schema failure'},
        'sequence': ['control', 'treatment'] * 3,
        'added_event_ids': RENT_IDS,
        'image_hashes': {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                         for p in cases['control']['image_paths']},
        'requests': {arm: payload(case) for arm, case in cases.items()},
        'references': 'Historical references remain unchanged and are not automatic semantic labels.',
    }


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def summarize(records):
    result = {}
    for arm in ('control', 'treatment'):
        group = [r for r in records if r['arm'] == arm]
        result[arm] = {
            'logical_runs': len(group),
            'first_attempt_usable': sum(r['run']['attempts'][0]['schema_valid'] for r in group),
            'final_usable': sum(r['run']['usable'] for r in group),
            'retry_recoveries': sum(r['run']['usable'] and not r['run']['attempts'][0]['schema_valid'] for r in group),
            'attempts': sum(len(r['run']['attempts']) for r in group),
            'empty_outputs': sum(a.get('raw_content') == '' and not a.get('provider_failure')
                                 for r in group for a in r['run']['attempts']),
            'provider_failures': sum(bool(a.get('provider_failure')) for r in group for a in r['run']['attempts']),
        }
    result['comparison_status'] = ('awaiting semantic review' if all(result[a]['final_usable'] >= 2
                                  for a in ('control', 'treatment')) else 'operationally inconclusive')
    result['warning'] = 'Availability is not semantic correctness. Three runs per arm are descriptive only.'
    return result


def review_rows(records):
    return [{'arm': r['arm'], 'logical_run': r['logical_run'], 'attempt': a['attempt'],
             'usable': a['schema_valid'], 'target_outcome': None,
             'allowed_target_outcomes': ['correct_supported_stream', 'unsupported_balance_linkage',
                                         'ambiguous_target', 'abstention'],
             'percentage': None, 'scope': None, 'bounds': None, 'image_value_and_target': None,
             'harmful_extra_assertions': None, 'supported_extras': None,
             'whole_bundle_assessment': None, 'evidence_and_rationale': None,
             'reviewer': None, 'review_status': 'pending' if a['schema_valid'] else 'output unavailable'}
            for r in records for a in r['run']['attempts']]


def execute(output, approved_by):
    if not approved_by or not approved_by.strip():
        raise ValueError('Record the human approving the documented rubric before execution')
    plan = prepare()
    cases = arms()
    frozen.load_env()
    if not os.environ.get('FEATHERLESS_API_KEY'):
        raise RuntimeError('FEATHERLESS_API_KEY is not configured')
    secret = os.environ['FEATHERLESS_API_KEY']

    def sanitize(value):
        if isinstance(value, str):
            return value.replace(secret, '[REDACTED]')
        if isinstance(value, dict):
            return {k: sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [sanitize(v) for v in value]
        return value

    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'manifest.json', sanitize({**plan, 'executed': True,
              'rubric_approved_by': approved_by, 'started_at': datetime.now(timezone.utc).isoformat()}))
    original = frozen.call_model
    records = []
    try:
        for index, arm in enumerate(plan['sequence'], 1):
            attempt_number = 0

            def captured_call(case, correction=None):
                nonlocal attempt_number
                attempt_number += 1
                prefix = f'{index:02d}_{arm}_attempt{attempt_number}'
                request = payload(case, correction)
                if attempt_number == 1 and request != plan['requests'][arm]:
                    raise RuntimeError('Input changed after manifest preparation')
                write_new(output / f'{prefix}_request.json', sanitize(request))
                try:
                    response, latency = original(case, correction)
                except Exception as exc:
                    write_new(output / f'{prefix}_error.json', sanitize({'type': type(exc).__name__, 'message': str(exc)}))
                    raise
                write_new(output / f'{prefix}_response.json', sanitize({'response': response, 'latency_seconds': latency}))
                return response, latency

            frozen.call_model = captured_call
            run = frozen.extract_once(cases[arm])
            record = sanitize({'arm': arm, 'logical_run': index, 'run': run})
            write_new(output / f'{index:02d}_{arm}_result.json', record)
            records.append(record)
    finally:
        frozen.call_model = original
    report = summarize(records)
    write_new(output / 'summary.json', report)
    write_new(output / 'claim_review_template.json', review_rows(records))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Make at most 12 model calls; default is offline preparation')
    parser.add_argument('--approved-by', help='Human who approved all conventions in RENT_HISTORY_EXPERIMENT.md')
    parser.add_argument('--output', type=Path, required=True, help='New file for preparation, new directory for a live run')
    args = parser.parse_args()
    if args.run:
        if not args.approved_by:
            parser.error('--run requires --approved-by after human rubric approval')
        print(json.dumps(execute(args.output, args.approved_by), indent=2))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_new(args.output, prepare())
        print(f'Offline plan saved: {args.output}; no model calls')


if __name__ == '__main__':
    main()
