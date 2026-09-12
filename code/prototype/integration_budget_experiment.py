"""Generous-budget API diagnostic: JSON mode on versus omitted, two calls each."""
import copy
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from . import extraction_experiment as frozen
from evidence import EvidenceBundle


def run():
    source = frozen.ARTIFACTS / 'rent_run_01/01_control_attempt1_request.json'
    baseline = json.loads(source.read_text())
    assert baseline['reasoning_effort'] == 'high'
    output = frozen.ARTIFACTS / 'integration_budget_01'
    frozen.load_env()
    secret = os.environ['FEATHERLESS_API_KEY']

    def clean(value):
        if isinstance(value, str): return value.replace(secret, '[REDACTED]')
        if isinstance(value, dict): return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list): return [clean(v) for v in value]
        return value

    def save(name, value):
        with (output / name).open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(clean(value), handle, indent=2)
            handle.write('\n')

    output.mkdir(exist_ok=False)
    save('manifest.json', {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'source': str(source.relative_to(frozen.ROOT)),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'sequence': ['json_mode', 'plain_mode', 'json_mode', 'plain_mode'], 'calls': 4, 'retries': 0,
        'support_source': 'https://featherless.ai/docs/completions',
        'decision_rule': '32768 output tokens, 600-second timeout. Compare JSON mode versus omitted response_format, same high reasoning and exact messages. Four calls, no retries; no semantic prompt changes.'})
    records = []
    for index, effort in enumerate(['json_mode', 'plain_mode', 'json_mode', 'plain_mode'], 1):
        payload = copy.deepcopy(baseline)
        payload['max_tokens'] = 32768
        if effort == 'plain_mode': payload.pop('response_format', None)
        assert {k: v for k, v in payload.items() if k not in ('max_tokens','response_format')} == {k: v for k, v in baseline.items() if k not in ('max_tokens','response_format')}
        save(f'{index:02d}_{effort}_request.json', payload)
        req = urllib.request.Request(frozen.ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers={
            'Authorization': 'Bearer ' + secret, 'Content-Type': 'application/json',
            'X-Title': 'HackerRank Orchestrate semantic extraction experiment',
            'HTTP-Referer': 'https://www.hackerrank.com/',
            'User-Agent': 'HackerRank-Orchestrate-Semantic-Experiment/1.0'})
        started = time.perf_counter()
        row = {'index': index, 'mode': effort, 'provider_failure': False,
               'nonempty_final': False, 'schema_valid': False}
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                envelope = json.loads(response.read().decode('utf-8'))
            save(f'{index:02d}_{effort}_response.json', envelope)
            choice = envelope['choices'][0]
            message = choice['message']
            content = message.get('content') or ''
            row.update(finish_reason=choice.get('finish_reason'), nonempty_final=bool(content.strip()),
                       reasoning_present=bool(message.get('reasoning')), usage=envelope.get('usage', {}))
            try:
                bundle = EvidenceBundle.model_validate(json.loads(content))
                row['schema_valid'] = True
                row['bundle'] = bundle.model_dump(mode='json')
            except Exception as exc:
                row['validation_error'] = str(exc)
        except Exception as exc:
            row.update(provider_failure=True, error_type=type(exc).__name__, error=str(exc))
        row['latency_seconds'] = time.perf_counter() - started
        save(f'{index:02d}_{effort}_result.json', row)
        records.append(row)
        print(json.dumps({k: v for k, v in row.items() if k not in ('bundle', 'validation_error', 'error')}), flush=True)
    save('summary.json', {effort: {
        'calls': 2,
        'nonempty_final': sum(r['nonempty_final'] for r in records if r['mode'] == effort),
        'schema_valid': sum(r['schema_valid'] for r in records if r['mode'] == effort),
        'provider_failures': sum(r['provider_failure'] for r in records if r['mode'] == effort)
    } for effort in ['json_mode', 'plain_mode']})


if __name__ == '__main__':
    run()
