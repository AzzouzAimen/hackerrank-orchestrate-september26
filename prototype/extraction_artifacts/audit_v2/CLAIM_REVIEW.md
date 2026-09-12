# Assistant claim review — pending human approval

All 63 saved emissions are listed below. Full field values, separate uncertainty/bound judgments, evidence IDs and source hashes are in [claim_review.json](claim_review.json). This table is a view of those annotations; supported meaning does not imply resolver-equivalent decomposition.

## experiment_20260912T155852Z.json / rep_user01 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| lifecycle_refund_event_99_of_event_98 | supported | correct | event_99 explicitly describes a settled reversal linked to event_98; event date is supplied, not invented. |
| lifecycle_retry_event_101_of_event_100 | incorrect | correct | event_101 is a settled card purchase linked to cancelled authorization event_100. No failed purchase/retry is stated; settlement_of is supported. |
| cash_class_event_100_cancelled_authorization | redundant | correct | Cancelled authorization is not available cash. historical_only restates the supplied cancelled state; no current cash is fabricated. |
| future_confirmation_event_103_salary | supported | correct | event_103 explicitly supplies Next confirmed salary, ZAR 23320 and 2024-03-15. Supported extra even though the reference chose ongoing stream status. |
## experiment_20260912T155852Z.json / rep_user07 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| rep_user07_stream_salary_ongoing_01 | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| rep_user07_future_payroll_2024-09-23_01 | unsupported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. INR 149000 is historically supported, not a confirmed future amount. Python may project it; extraction may not assert confirmation. |
| rep_user07_sched_amend_payroll_2024-09-23_01 | supported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved. |
## experiment_20260912T155852Z.json / rep_user16 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| stream_status_salary_user16 | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| amount_amendment_rent_increase_12pct | ambiguous | ambiguous: outstanding balance is not established as renewed lease stream | message_12 states a 12% renewed monthly lease increase. Input omits every Monthly rent event, while the reference demands that exact selector. Linking it to event_1442 is not established; cannot attribute the target failure solely to the model. |
| future_confirmation_rent_event_1442 | ambiguous | correct | Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference. Same bundle also extracts Balance Due. Separate row-null and image-value claims have supported provenance but are not equivalent consolidated resolver inputs. |
| image_02_total_amount_to_be_received | incorrect | correct | image_02 shows total 200000, received 100000, Balance Due 100000. The gross total is not the current amount due; numeric OCR itself is correct. |
| image_02_amount_received | supported | correct image link; historical payment is not scheduled debit | Amount Received INR 100000 is visibly supported. This is a supported extra receipt field, not a license to overwrite future outstanding debt; the engine already rejects that use. |
| image_02_balance_due | supported | correct | Balance Due INR 100000 is visible in image_02 and image metadata links event_1442. Historical receipt period does not amend the supplied scheduled settlement date. |
## experiment_20260912T155852Z.json / rep_user21 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| salary_stream_status_user21 | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| salary_schedule_monthly_15th_user21 | ambiguous | correct | Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent. |
| salary_amount_2256_usd_user21 | ambiguous | correct | Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent. |
| future_salary_2026_04_15_user21 | supported | correct | Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference. |
## experiment_20260912T155852Z.json / rep_user25 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| rep_user25_salary_stream_status_ongoing | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| rep_user25_salary_schedule_monthly_15th | ambiguous | correct | Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent. |
| rep_user25_next_salary_confirmed_2024_03_15 | supported | correct | Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference. |
## experiment_20260912T155852Z.json / synthetic_unknown_obligation / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_confirmation_syn_event_unknown_dining | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
## experiment_20260912T155852Z.json / synthetic_possible_duplicate / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| syn_lifecycle_possible_duplicate_b_of_a | supported | correct | syn_msg_duplicate explicitly says b might duplicate a, investigation open. Correct child/parent, possible relation and uncertain confirmation are preserved. |
## experiment_20260912T155852Z.json / synthetic_conflict_two_streams / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| amt_amend_dinner_next_month | ambiguous | correct Dinner identity; event-restricted scope needs adjudication | Newer same-source correction supports USD 25 for next month only; Lunch is unchanged. Both target the Dinner identity. Explicit syn_dinner ID restricts the selector to history, it does not broaden it. It may denote stream membership, but equivalence to an open future selector is not established; do not score it automatically correct or hallucinated. |
## experiment_20260912T155852Z.json / rep_user07 / run 2

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| sched_amend_salary_2024-09-23 | unsupported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved. effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved. |
| future_conf_salary_2024-09-23 | supported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. |
| stream_status_salary_monthly | ambiguous | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. Future permanence is not guaranteed. Reference confirmed versus model uncertain changes resolver eligibility; neither certainty convention is independently approved. |
## experiment_20260912T155852Z.json / rep_user07 / run 3

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| fact_user07_salary_stream_ongoing | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| fact_user07_sept_payroll_date_amendment | unsupported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved. effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved. |
| fact_user07_sept_payroll_future_confirmation | supported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. |
## experiment_20260912T155852Z.json / synthetic_unknown_obligation / run 2

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_conf_syn_event_unknown | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
## experiment_20260912T155852Z.json / synthetic_unknown_obligation / run 3

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_confirmation_syn_event_unknown | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
## experiment_20260912T160401Z.json / rep_user01 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| lifecycle_refund_event_99_of_event_98 | incorrect | incorrect: parent also asserted as child | event_99 explicitly describes a settled reversal linked to event_98; event date is supplied, not invented. Parent in affected_event_ids asserts a self-relationship; provenance may list both legs, but the child target should not. |
| lifecycle_retry_event_101_of_event_100 | incorrect | incorrect: parent also asserted as child | event_101 is a settled card purchase linked to cancelled authorization event_100. No failed purchase/retry is stated; settlement_of is supported. Parent in affected_event_ids asserts a self-relationship; provenance may list both legs, but the child target should not. |
| cash_class_event_100_cancelled | redundant | correct | Cancelled authorization is not available cash. historical_only restates the supplied cancelled state; no current cash is fabricated. |
| future_salary_event_103 | supported | correct | event_103 explicitly supplies Next confirmed salary, ZAR 23320 and 2024-03-15. Supported extra even though the reference chose ongoing stream status. |
## experiment_20260912T160401Z.json / rep_user07 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| fact_user07_salary_stream_ongoing | ambiguous | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. Future permanence is not guaranteed. Reference confirmed versus model uncertain changes resolver eligibility; neither certainty convention is independently approved. |
| fact_user07_september_payroll_date_change | unsupported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved. effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved. |
| fact_user07_september_payroll_expected | supported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. |
| fact_user07_september_payroll_pending_credit | incorrect | correct | Evidence confirms future salary, not a pending bank credit. pending_credit is a resolver exclusion, so ordinary-language not-yet-paid is not equivalent to this cash classification. |
## experiment_20260912T160401Z.json / rep_user21 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| rep_user21_salary_stream_status_001 | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| rep_user21_salary_future_confirmation_001 | supported | correct | Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference. |
| rep_user21_salary_cash_settled_001 | redundant | correct | The targeted salary rows are settled cash; bounds bracket exactly the supplied historical settlements. |
| rep_user21_salary_cash_pending_001 | incorrect | correct | Evidence confirms future salary, not a pending bank credit. pending_credit is a resolver exclusion, so ordinary-language not-yet-paid is not equivalent to this cash classification. |
## experiment_20260912T160401Z.json / rep_user25 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| fact_user25_salary_stream_status | supported | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. |
| fact_user25_salary_schedule_monthly | ambiguous | correct | Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent. |
| fact_user25_salary_amount_per_cycle | ambiguous | correct | Regular equal salary rows support an observed amount/monthly pattern and the explicit next salary. No change is stated. Encoding observation as ongoing amendment is not automatically a hallucination, but can change resolver behavior and exceeds the extraction/forecast boundary if treated as permanent. |
| fact_user25_next_salary_confirmation | supported | correct | Supplied scheduled event explicitly supplies the amount/currency/date/direction, with null amount preserved for event_1442. Supported restatement omitted by reference. |
| fact_user25_next_salary_pending_credit | incorrect | correct | Evidence confirms future salary, not a pending bank credit. pending_credit is a resolver exclusion, so ordinary-language not-yet-paid is not equivalent to this cash classification. |
## experiment_20260912T160401Z.json / unused_real_image03 / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| image_03_amount_paid_41272.00_inr | supported | correct | Direct visual audit: Cash Paid 41272.00, same numeric value as 41272. Event supplies INR and 2026-02-27; receipt date agrees. effective_from is not fabricated. |
| image_03_net_amount_41272.0_inr | incorrect | correct | Net Amount 41272.0 equals Cash Paid 41272.00 on the receipt and the linked event is settled. It does not establish a current amount due. Numeric OCR and currency are correct. |
## experiment_20260912T160401Z.json / synthetic_unknown_obligation / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_confirmation:syn_event_unknown:dining | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
## experiment_20260912T160401Z.json / synthetic_possible_duplicate / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| lifecycle_syn_charge_b_possible_duplicate_of_syn_charge_a | supported | correct | syn_msg_duplicate explicitly says b might duplicate a, investigation open. Correct child/parent, possible relation and uncertain confirmation are preserved. |
## experiment_20260912T160401Z.json / synthetic_conflict_two_streams / run 1

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| amt_amend_dinner_next_month | ambiguous | correct Dinner identity; event-restricted scope needs adjudication | Newer same-source correction supports USD 25 for next month only; Lunch is unchanged. Both target the Dinner identity. Explicit syn_dinner ID restricts the selector to history, it does not broaden it. It may denote stream membership, but equivalence to an open future selector is not established; do not score it automatically correct or hallucinated. |
## experiment_20260912T160401Z.json / rep_user07 / run 2

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| fact_user07_salary_stream_ongoing | ambiguous | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. Future permanence is not guaranteed. Reference confirmed versus model uncertain changes resolver eligibility; neither certainty convention is independently approved. |
| fact_user07_sept_payroll_date_change | unsupported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved. |
| fact_user07_sept_payroll_expected | unsupported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. INR 149000 is historically supported, not a confirmed future amount. Python may project it; extraction may not assert confirmation. |
## experiment_20260912T160401Z.json / rep_user07 / run 3

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| fact_user07_sched_amend_sept_payroll | unsupported | correct | message_05 explicitly replaces the next payroll date with 2024-09-23; supplied salary history identifies Payroll credit. The message does not say the old schedule resumes afterward; one_cycle is an unsupported duration assertion despite sometimes listing duration unresolved. effective_from copies the payment date; this is not an invented date, but amendment applicability is unresolved. |
| fact_user07_future_conf_sept_payroll | supported | correct | message_05 confirms a future salary on 2024-09-23, but supplies no amount; INR is established by the history. |
| fact_user07_stream_status_salary | ambiguous | correct | Five supplied salary observations establish a recurring history; first observed date is a valid lower observed bound, not an invented inception. Explicit IDs determine membership even when selector description differs for Next confirmed salary. Future permanence is not guaranteed. Reference confirmed versus model uncertain changes resolver eligibility; neither certainty convention is independently approved. |
## experiment_20260912T160401Z.json / synthetic_unknown_obligation / run 2

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_confirmation_syn_event_unknown | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
| amount_unresolved_syn_event_unknown | redundant | correct | Restates the same unknown amount or date already present in future confirmation. No value or duration invented. Equivalent financial meaning; extra amendment objects are not promised to be resolver-equivalent. |
| schedule_unresolved_syn_event_unknown | redundant | correct | Restates the same unknown amount or date already present in future confirmation. No value or duration invented. Equivalent financial meaning; extra amendment objects are not promised to be resolver-equivalent. |
## experiment_20260912T160401Z.json / synthetic_unknown_obligation / run 3

| Fact | Judgment | Target | Rationale |
|---|---|---|---|
| future_confirmation_syn_event_unknown_dining | supported | correct | syn_msg_unknown confirms the obligation but explicitly leaves amount and date unset. Both remain null; currency/direction and target agree with the event. |
