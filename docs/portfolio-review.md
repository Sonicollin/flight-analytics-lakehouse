# Final portfolio review

The original project had useful source ingestion and tests, but its application generations, broken imports, hard-coded dbt path, unsupported cross-source join and stale generated output made it difficult to tell what actually ran. The completed project now has one execution path and an explicit separation between historical reported flights and aircraft-state observations.

As an Analytics Engineering portfolio, its strongest evidence is the combination of documented grains, source-specific analytical models, transparent metric denominators, source-row lineage, rerun behavior, Pydantic validation and real dlt/dbt integration tests. The live verification record supports the claim that the pipeline works beyond mocked unit tests. Generated files, duplicate entry points, empty placeholder logic and unsupported optimization claims have been removed.

An interviewer should be able to trace a carrier-month metric from BTS through Parquet, staging and flight outcomes, explain why unknown arrival delay is not counted as on time, and explain why a repeated OpenSky observation is merged while a later observation is retained. The absence of a BTS/OpenSky join is an intentional modeling decision.

The remaining limits are explicit: local single-writer storage, eager monthly CSV conversion, one live month/snapshot verified, no scheduler or automatic retry policy, no token-refresh implementation, no evidence of distributed scale and no route-mix-adjusted airline ranking. This is a defensible local portfolio project; it does not establish production operations experience.

Suggested interview walkthrough: run the offline demo, inspect the two marts, trace the 15-minute fixture through the intermediate model, then inspect the real-data verification record and discuss where a larger operational system would need a different design.
