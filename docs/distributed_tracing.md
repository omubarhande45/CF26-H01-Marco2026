# Distributed tracing

Every query carries `query_id`, `correlation_id`, `trace_id` from dashboard/gateway through each agent. Audit rows include these IDs. Logs redact patient identifiers (`shared/tracing.safe_log`).
