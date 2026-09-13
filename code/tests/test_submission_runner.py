from pathlib import Path

from submission_runner import decide, fail_closed, run, OUTPUT_FIELDS


def fixture():
    request={"request_id":"r","user_id":"u","request_date":"2026-09-01","request_type":"test","requested_amount":"10",
             "desired_completion_date":"2026-09-10","allows_partial_payment":"false","request_text":"test"}
    profile={"user_id":"u","home_currency":"USD","current_available_balance":"100","minimum_balance_to_keep":"20",
             "financial_priorities":"","expense_categories_to_protect":"","expense_categories_user_is_willing_to_reduce":"",
             "expense_categories_user_is_willing_to_stop":"","payment_methods_user_will_consider":"full_payment","max_installment_months":""}
    tables={"financial_profiles":[profile],"financial_events":[],"exchange_rates":[],"request_payment_options":[],"messages":[],"images":[]}
    return request,tables


def test_no_semantic_evidence_requires_no_model_call(tmp_path: Path):
    request,tables=fixture()
    def forbidden(*args): raise AssertionError("model call forbidden")
    result,audit=decide(tmp_path,request,tables,forbidden,tmp_path/'a')
    assert result["recommended_payment_method"] == "full_payment"
    assert audit["usage"]["calls"] == 0


def test_extraction_failure_is_fail_closed(tmp_path: Path):
    request,tables=fixture(); tables["messages"]=[{"message_id":"m","user_id":"u","request_id":"r","sent_at":"2026-08-01","message_text":"unknown bill"}]
    result,audit=decide(tmp_path,request,tables,lambda case,path:{"usable":False,"attempts":[]},tmp_path/'a')
    assert result["amount_safe_to_pay"] == "0"
    assert result["recommended_payment_method"] == "not_recommended"
    assert audit["blocked"]


def test_fail_closed_has_exact_output_contract():
    request,_=fixture(); result=fail_closed(request,["unknown debit"]).model_dump()
    assert tuple(result) == OUTPUT_FIELDS


def test_decision_cache_prevents_duplicate_model_call(tmp_path: Path):
    request,tables=fixture(); tables["messages"]=[{"message_id":"m","user_id":"u","request_id":"r","sent_at":"2026-08-01","message_text":"unknown bill"}]
    calls=[]
    def unavailable(case,path): calls.append(case); return {"usable":False,"attempts":[]}
    decide(tmp_path,request,tables,unavailable,tmp_path/'a')
    decide(tmp_path,request,tables,unavailable,tmp_path/'a')
    assert len(calls)==1
