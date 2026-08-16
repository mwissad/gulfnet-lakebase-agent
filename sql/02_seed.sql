-- GulfNet synthetic UAE seed data

INSERT INTO gulfnet.plans (plan_id, name_en, name_ar, type, monthly_fee_aed, data_gb, voice_minutes, roaming_gcc, roaming_intl, description_en, description_ar) VALUES
('GN-PRE-25', 'GulfStart 25', 'غلف ستارت 25', 'prepaid', 25.00, 8, 100, FALSE, FALSE,
 'Entry prepaid: 8GB + 100 local minutes. No roaming.', 'باقة مسبقة الدفع للمبتدئين'),
('GN-POST-99', 'GulfMax 99', 'غلف ماكس 99', 'postpaid', 99.00, 40, 500, TRUE, FALSE,
 'Popular postpaid with GCC roaming (KSA, Oman, Bahrain, Kuwait, Qatar).', 'باقة شهرية مع تجوال دول الخليج'),
('GN-VIP-299', 'GulfElite 299', 'غلف إيليت 299', 'postpaid', 299.00, 150, NULL, TRUE, TRUE,
 'VIP unlimited voice, 150GB, worldwide roaming packs included.', 'باقة كبار الشخصيات مع تجوال عالمي'),
('GN-SME-149', 'GulfBiz 149', 'غلف بيز 149', 'enterprise', 149.00, 60, 1000, TRUE, FALSE,
 'SME plan with shared data pool eligibility and priority care.', 'باقة للأعمال الصغيرة'),
('GN-IOT-49', 'GulfIoT 49', 'غلف إنترنت الأشياء 49', 'enterprise', 49.00, 5, 0, FALSE, FALSE,
 'Low-data IoT / machine-to-machine lines.', 'باقة إنترنت الأشياء')
ON CONFLICT (plan_id) DO NOTHING;

INSERT INTO gulfnet.subscribers (account_id, msisdn, full_name, segment, plan_id, emirate, language_pref, channel_pref, arpu_aed, churn_risk, status) VALUES
('ACC-1001', '+971501234567', 'Layla Al Mansoori', 'VIP', 'GN-VIP-299', 'Dubai', 'ar', 'whatsapp', 312.50, 'low', 'active'),
('ACC-1002', '+971559876543', 'Omar Hassan', 'SME', 'GN-SME-149', 'Abu Dhabi', 'en', 'sms', 168.00, 'medium', 'active'),
('ACC-1003', '+971521112233', 'Fatima Khan', 'prepaid', 'GN-PRE-25', 'Sharjah', 'en', 'sms', 28.00, 'high', 'active'),
('ACC-1004', '+971504445566', 'James Whitfield', 'tourist', 'GN-POST-99', 'Dubai', 'en', 'email', 99.00, 'low', 'active'),
('ACC-1005', '+971567778889', 'Marina Logistics IoT', 'enterprise', 'GN-IOT-49', 'Dubai', 'en', 'email', 49.00, 'low', 'active'),
('ACC-1006', '+971502223344', 'Sara Abdullah', 'VIP', 'GN-VIP-299', 'Dubai', 'ar', 'whatsapp', 340.00, 'low', 'active'),
('ACC-1007', '+971558889900', 'Rashid Al Nuaimi', 'SME', 'GN-SME-149', 'Ajman', 'ar', 'sms', 155.00, 'medium', 'active')
ON CONFLICT (account_id) DO NOTHING;

INSERT INTO gulfnet.usage_daily (account_id, usage_date, data_gb, voice_minutes, roaming_data_gb, roaming_country) VALUES
('ACC-1001', CURRENT_DATE - 3, 4.2, 45, 0.8, 'SA'),
('ACC-1001', CURRENT_DATE - 2, 3.1, 20, 0, NULL),
('ACC-1001', CURRENT_DATE - 1, 5.5, 60, 0, NULL),
('ACC-1002', CURRENT_DATE - 2, 2.0, 120, 0, NULL),
('ACC-1002', CURRENT_DATE - 1, 2.4, 90, 0.2, 'OM'),
('ACC-1003', CURRENT_DATE - 1, 7.5, 40, 0, NULL),
('ACC-1004', CURRENT_DATE - 1, 1.2, 10, 0.5, 'GB'),
('ACC-1006', CURRENT_DATE - 5, 2.0, 15, 1.5, 'SA'),
('ACC-1006', CURRENT_DATE - 1, 6.0, 30, 0, NULL)
ON CONFLICT (account_id, usage_date) DO NOTHING;

INSERT INTO gulfnet.network_events (emirate, cell_area, severity, started_at, ended_at, description, affected_tech) VALUES
('Dubai', 'Dubai Marina', 'degraded', NOW() - INTERVAL '2 hours', NULL,
 'Elevated packet loss on 5G mid-band sectors near Marina Walk. Voice OK; data slow.', '5G'),
('Dubai', 'Business Bay', 'info', NOW() - INTERVAL '1 day', NOW() - INTERVAL '20 hours',
 'Scheduled maintenance completed successfully.', '5G'),
('Abu Dhabi', 'Al Reem Island', 'outage', NOW() - INTERVAL '30 minutes', NULL,
 'Site power issue affecting 4G/5G. Field crew dispatched.', '4G/5G'),
('Sharjah', 'Al Majaz', 'info', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '2 hours',
 'Capacity upgrade completed.', '5G');

INSERT INTO gulfnet.kb_documents (doc_id, title, category, language, source_uri) VALUES
('DOC-ROAM-GCC', 'GCC Roaming Guide 2026', 'roaming', 'en', 'volume://gulfnet/kb/roaming-gcc.md'),
('DOC-ROAM-SA', 'Saudi Arabia Roaming Packs', 'roaming', 'en', 'volume://gulfnet/kb/roaming-sa.md'),
('DOC-PLAN-VIP', 'GulfElite 299 Plan Terms', 'plans', 'en', 'volume://gulfnet/kb/plan-vip.md'),
('DOC-PLAN-POST', 'GulfMax 99 Plan Terms', 'plans', 'en', 'volume://gulfnet/kb/plan-post.md'),
('DOC-SLA-VIP', 'VIP Care SLA', 'sla', 'en', 'volume://gulfnet/kb/sla-vip.md'),
('DOC-5G-COV', '5G Coverage Notes UAE', 'network', 'en', 'volume://gulfnet/kb/5g-coverage.md'),
('DOC-RETENTION', 'Retention Offers Playbook', 'retention', 'en', 'volume://gulfnet/kb/retention.md'),
('DOC-AR-FAQ', 'أسئلة شائعة عن التجوال', 'roaming', 'ar', 'volume://gulfnet/kb/roaming-ar.md')
ON CONFLICT (doc_id) DO NOTHING;

INSERT INTO gulfnet.kb_chunks (doc_id, chunk_index, content, metadata) VALUES
('DOC-ROAM-GCC', 0,
 'GulfNet GCC roaming covers Saudi Arabia (KSA), Oman, Bahrain, Kuwait, and Qatar. GulfMax 99 and higher include daily GCC roaming allowances: 1GB/day at no extra charge for the first 7 travel days per month. Beyond that, AED 15/day for 1GB.',
 '{"topic":"gcc_roaming"}'),
('DOC-ROAM-SA', 0,
 'Riyadh / KSA travel: customers on GulfElite 299 get unlimited GCC roaming voice and 5GB/day data in Saudi Arabia. GulfMax 99 gets 1GB/day for 7 days. Prepaid GulfStart 25 has no roaming — recommend upgrading to GulfMax 99 before travel or buying a KSA day pass (AED 25 for 2GB).',
 '{"topic":"ksa_roaming","city":"Riyadh"}'),
('DOC-PLAN-VIP', 0,
 'GulfElite 299 (AED 299/month): 150GB UAE data, unlimited local voice, GCC + international roaming packs, priority VIP care queue (15-minute first response SLA), complimentary airport lounge Wi-Fi partner access.',
 '{"plan_id":"GN-VIP-299"}'),
('DOC-PLAN-POST', 0,
 'GulfMax 99 (AED 99/month): 40GB UAE data, 500 local minutes, GCC roaming included (see GCC Roaming Guide). No worldwide roaming — add International Day Pass AED 40 for 1GB.',
 '{"plan_id":"GN-POST-99"}'),
('DOC-SLA-VIP', 0,
 'VIP Care SLA: first human response within 15 minutes during 08:00–22:00 GST. Network degradation impacting VIP accounts in Dubai Marina or Downtown must trigger an automatic VIP impact report within 10 minutes. WhatsApp and Arabic SMS are preferred notification channels for VIP Arabic-preferring customers.',
 '{"segment":"VIP"}'),
('DOC-5G-COV', 0,
 'UAE 5G coverage is strong across Dubai Marina, Downtown, Business Bay, Abu Dhabi Corniche, and Al Reem. Temporary degradation may occur during waterfront events. Check network_events for live status. Voice typically remains available on 4G fallback when 5G data is degraded.',
 '{"topic":"coverage"}'),
('DOC-RETENTION', 0,
 'High churn-risk prepaid customers (>80% data used mid-cycle): offer GulfMax 99 with first month at AED 49. SME medium risk: offer +20GB booster for AED 20. Always confirm language and channel preferences before sending offers.',
 '{"topic":"retention"}'),
('DOC-AR-FAQ', 0,
 'التجوال في المملكة العربية السعودية: باقة غلف إيليت 299 تشمل بيانات يومية في السعودية. باقة غلف ماكس 99 تشمل 1 جيجا يوميا لأول 7 أيام. باقة غلف ستارت 25 لا تشمل التجوال.',
 '{"topic":"ksa_roaming","lang":"ar"}');
