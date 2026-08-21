# Logging and retention

LiteLLM is configured to keep **usage metadata** and drop **prompt/response bodies**.

| Field | Stored |
|---|---|
| Employee ID / key alias | yes |
| Timestamp | yes |
| Model alias + provider | yes |
| Prompt / completion / total tokens | yes |
| Cost | yes |
| Status / latency | yes |
| Full prompt or completion text | **no** (`turn_off_message_logging`, `store_prompts_in_spend_logs: false`) |

Open WebUI stores chat threads for the signed-in employee so the product works. That is not a company-wide prompt archive. Disable or delete the Open WebUI user on offboarding if those threads must go.

Retention: spend rows stay as long as the Postgres backups do (7/4/3 unless you shorten it). There is no separate log shipper.
