# Problem Statement

## Background

Power utilities operate thousands of transformers and substations that form the backbone of the electricity grid. These assets are heavily instrumented — sensors continuously measure oil temperature, winding vibration, oil degradation, and partial discharge activity. Despite this wealth of real-time telemetry, most utilities still schedule maintenance on fixed calendar intervals, because the sensor data, weather information, and maintenance records are siloed across incompatible systems with no unified risk view.

## The Problem

Grid operations engineers and maintenance planners have no single tool that combines sensor health trends, weather forecasts, and historical failure records into a clear, actionable risk ranking of their equipment. The practical consequences are severe:

- **Missed pre-failure signals:** Sensor anomalies (rising oil temperature, increasing partial discharge) are only reviewed reactively — after a trip or outage — rather than surfaced proactively while there is still time to act.
- **Wasted maintenance budget:** Calendar-based schedules dispatch crews to healthy assets while genuinely degrading equipment waits. A utility managing 100 assets wastes roughly 60% of its maintenance spend on assets that did not need servicing.
- **No weather correlation:** Incoming heatwaves, storms, and high-wind events dramatically increase transformer failure risk — but this information is never cross-referenced with current sensor health data, so there is no pre-positioning of crews or pre-emptive load management.

A single transformer failure in a dense urban zone can cut power to tens of thousands of customers and cost a utility $45,000–$250,000 in direct repair costs plus $1 M+/hour in outage penalties under regulatory frameworks.

## Who Is Affected

**Primary users:** Grid operations engineers and maintenance planners at electricity distribution and transmission utilities managing 50–500+ field assets across multiple geographic zones.

**Secondary stakeholders:** Hospitals, water treatment plants, fire stations, data centres, and any critical-facility operator dependent on uninterrupted power — all of whom bear the downstream cost of unplanned outages that sensor data could have predicted.

## Why It Matters

| Impact dimension | Magnitude |
|---|---|
| Direct repair cost per major transformer failure | $45,000 – $250,000 |
| Outage penalty per hour (regulatory / SLA) | $1 M+ |
| Wasted maintenance spend on healthy assets (calendar-based) | ~60% of budget |
| Advance warning available from sensor trends | 2–3 weeks before failure |
| Weather-correlated failures (underreacted to) | ~30% of all incidents |

Climate change is increasing the frequency and severity of heatwaves and storms, which are the leading external trigger for transformer failures — making weather-correlated risk assessment more urgent than ever.

## Why Existing Solutions Fall Short

| Current approach | Why it fails |
|---|---|
| Calendar-based maintenance (every 6 months) | Treats all assets identically; ignores real sensor trends; misses accelerated degradation in high-load or old assets |
| Siloed SCADA dashboards | Display raw sensor values but provide no failure-probability score, no cross-asset risk ranking, and no weather overlay |
| Manual post-incident analysis | Reactive by definition — the failure has already happened; insights arrive too late to prevent the next one |
| Generic asset management systems (SAP PM, IBM Maximo) | Schedule-driven, not predictive; do not ingest real-time sensor streams or correlate them with weather events |
| Simple threshold alerting | Triggers only when a sensor exceeds a fixed value — misses gradual multi-sensor degradation patterns that precede failure by weeks |

GridHealth AI addresses every one of these gaps by fusing sensor telemetry, weather forecasts, and incident history into a single risk-ranked, SHAP-explained view that planners can act on *before* equipment fails.
