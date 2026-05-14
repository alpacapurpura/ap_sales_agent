# T-fe-6 impl-log

**Ticket:** T-fe-6 — cohort/community/subscriptions/audit dashboards
**Tools:** Write (dashboard client components), Read (subscription.types.ts, community.types.ts, cohort.types.ts)
**Iterations:** 1 (tsc clean)
**Notes:** All dashboard views follow Server page -> Client component split (tessl__nextjs-app-router-modularization). SubscriptionsAdminClient uses formatMrr util. CommunityAuditClient uses AuditFilterSchema for filter form. DunningActiveBanner wired with real dunning count from useSubscriptionMetrics hook.
