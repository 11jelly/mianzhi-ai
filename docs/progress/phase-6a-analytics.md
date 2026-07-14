# Phase 6A: Growth Analytics

## Goals

Build a personal growth analytics center based on completed interview reports.
The page helps users review score trends, latest ability distribution, current
weakest dimension, improvement-plan summaries, and historical reports.

## Data Sources

- `interview_sessions`
- `interview_reports`
- `interview_knowledge_base_links`
- `knowledge_bases`

No new database table or Alembic migration is required.

## Aggregation Rules

- Include only sessions owned by the current authenticated user.
- Include only `COMPLETED` sessions.
- Include only sessions that have an `interview_reports` row.
- Use `interview_reports.created_at` for trend ordering and date filtering.
- Compute `weakest_dimension` from the latest up to 5 reports by averaging:
  - `logic_score`
  - `technical_score`
  - `expression_score`
  - `project_depth_score`
- Improvement suggestions are extracted from the latest report's existing
  `improvement_plan`; no LLM call is made.

## API

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/trend?days=30|90|180|365&target_role=...`
- `GET /api/v1/analytics/history?page=1&page_size=10&target_role=...`

All endpoints require JWT authentication and only return the current user's
analytics. Responses do not expose raw answers, knowledge-base document text,
embeddings, prompt content, or secret configuration.

## Page

Frontend route: `/growth`

The page includes:

- Overview cards for completed interview count, average overall score, weakest
  ability, and latest score.
- Latest ability radar chart using existing native ECharts radar rendering.
- Growth trend chart using native ECharts line series.
- Weakest ability and improvement-plan summaries.
- Historical interview list with linked knowledge-base names and report links.
- Empty state with a "create interview" entry when no completed report exists.

## Charts

- Radar dimensions:
  - Logic structure, max 25
  - Technical accuracy, max 30
  - Expression clarity, max 20
  - Project depth, max 25
- Trend chart includes overall score and the four ability scores.
- Empty chart data renders an empty state instead of throwing runtime errors.

## Permission Isolation

All analytics SQL queries filter by `interview_sessions.user_id`.
Other users' sessions and reports are excluded by construction.

## Automated Tests

Added `backend/tests/test_phase6a_analytics.py`, covering:

- Empty overview state.
- Counting only completed sessions with reports.
- Excluding `IN_PROGRESS`, `READY_FOR_REPORT`, and reportless sessions.
- Overview averages and latest report.
- Weakest dimension from the latest five reports.
- Trend ordering and filters.
- History pagination and knowledge-base names.
- User isolation.

## Manual Test Steps

1. Log in.
2. Complete at least one interview and generate a report.
3. Open `/growth` or click "成长分析" in the top navigation.
4. Confirm overview cards show completed count and average score.
5. Confirm the latest radar chart renders.
6. Switch trend range between 30, 90, 180, and 365 days.
7. Use the target-role filter and confirm the trend chart and history table only
   show that role.
8. Clear the target-role filter and confirm all completed roles are visible again.
9. Confirm history rows link back to `/interviews/{session_id}`.

## Known Limits

- Analytics are deterministic and report-based; they do not infer new insights
  beyond persisted report data.
- Trend and history filters support day range plus exact target role.
- The frontend table currently displays the first page of history.

## Next Phase Suggestions

- Add role grouping and comparison across interview types.
- Add pagination controls to the frontend history table.
- Export analytics as a local report.

## Suggested Git Commit Message

```text
feat: add growth analytics center
```
