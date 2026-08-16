# Golden demo transcripts — GulfNet Care Copilot

## Demo A — Memory + Search (roaming)

**CSR user_id:** `csr-demo-layla`

1. User: `Look up +971501234567. What's their plan and last roaming?`
   - Tools: `lookup_subscriber`, `get_usage_summary`
   - Expect: Layla Al Mansoori, VIP, GulfElite 299, recent KSA roaming.

2. User: `They'll visit Riyadh next week — what roaming options apply?`
   - Tools: `search_knowledge` (KSA / GCC roaming), optionally `recommend_plan`
   - Expect: GulfElite includes GCC/KSA daily data; cite KB chunk.

3. User: `Prefer WhatsApp updates in Arabic from now on.`
   - Tools: `save_user_memory`
   - Expect: memory keys like `channel_pref` / `language_pref`.

4. New thread, same user_id: `What do you remember about Layla's preferences?`
   - Tools: `get_user_memory`
   - Expect: Arabic + WhatsApp recalled.

---

## Demo B — Orchestration (VIP outage impact)

1. User: `There's a Dubai Marina degradation — impact on VIP accounts?`
   - Tools: `check_network_status`, `enqueue_ops_task` with
     `{"emirate":"Dubai","cell_area":"Dubai Marina"}`
   - Expect: task_id returned.

2. User: `What's the status of that task?` (paste task_id)
   - Tools: `get_task_status`
   - Expect: completed report with VIP list (Layla, Sara) + recommended actions.

3. Open ops dashboard: `/ops/dashboard`
   - Expect: live counts via SSE; completed `vip_outage_impact` row.

---

## Demo C — Retention

1. User: `Find high churn-risk prepaid customers and draft offers.`
   - Tools: `enqueue_ops_task` `churn_offer_batch` or direct recommend flow
   - Expect: Fatima Khan / GulfMax 99 promo at AED 49 first month.
