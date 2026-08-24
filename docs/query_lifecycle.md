# Query lifecycle

CREATED → VALIDATING → PLANNING → DISPATCHING → RUNNING → AGGREGATING → PRIVACY_CHECK → COMPLETED  

Terminal alternatives: PARTIAL, SUPPRESSED, DENIED, FAILED, TIMEOUT, CANCELLED.  

`POST /queries/{id}/cancel` sets CANCELLED and blocks COMPLETE.  
`POST /queries/{id}/execute-async` returns `{status: RUNNING}` while sync `execute` remains.
