# OC3 Source-Metadata Autonomous Recovery Production Specification 006

Status: **PROSPECTIVE RUN-005 PREPARATION; NOT EXECUTABLE**.

The Run-005 transport implementation consists of the bounded streaming-accounting primitive and the prospective material executor. Request intent precedes HTTP handoff. Complete and partial paths are distinct. Promotion is atomic only after successful EOF and, when present, exact `Content-Length` agreement. Parser execution occurs only after promotion.

`DATALAB_TRANSPORT_FAILURE` terminals preserve exact action totals and per-query observations. Parser failures after a complete response preserve transport totals and report zero accepted source values. The 300-second autonomous timeout remains unchanged; the separately approved 600-second timeout belongs only to the manual workflow.

Run-005 preparation state is `TRANSPORT_FAILURE_ACCOUNTING_REPAIRED / WAITING_FOR_MANUAL_ACQUISITION_AUDIT`. Execution is `NOT_STARTED`. No candidate or final authorization exists. A future evidence-ingestion candidate, if justified by the offline audit, must be separately frozen and must use request class `OFFLINE`, zero request/body reservation, and immutable audit bindings.

