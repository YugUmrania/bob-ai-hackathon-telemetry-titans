# Problem Statement

## Background

Power utilities operate thousands of transformers and substations that are the backbone of the electricity grid. These assets are instrumented with sensors that continuously measure oil temperature, winding vibration, oil quality, and partial discharge activity. Despite this wealth of real-time data, most utilities still schedule maintenance on fixed calendar intervals — not because the technology to do better doesn't exist, but because the data is siloed across SCADA systems, weather services, and maintenance records with no unified risk view.

## The Problem

Grid operations engineers and maintenance planners at power utilities have no single tool that combines sensor health data, weather forecasts, and historical failure records into a clear, actionable risk ranking of their equipment. As a result:

- Failure-prone assets are missed until they cause an outage, because sensor anomalies are only reviewed manually and reactively.
- Maintenance crews are dispatched on calendar schedules, wasting resources on healthy equipment while genuinely degrading equipment waits.
- Incoming weather events (heatwaves, storms, high winds) that dramatically increase transformer failure risk are never cross-referenced with current sensor health — so no pre-positioning of crews or pre-emptive load-shedding happens.

A single transformer failure in a dense urban zone can cut power to tens of thousands of customers and cost a utility $1 M+ per hour in penalties, emergency repair costs, and reputational damage.

## Who is Affected

**Primary users:** Grid operations engineers and maintenance planners at electricity distribution and transmission utilities who manage 50–500+ field assets across multiple geographic zones.

**Secondary stakeholders:** City infrastructure operators, hospitals, data centres, and any critical-facility operator dependent on uninterrupted power — all of whom bear the downstream cost of unplanned outages caused by equipment failures that sensor data could have predicted.

## Why It Matters

- **Financial:** A single major transformer failure costs $45 000–$250 000 in direct repair costs and can trigger $1 M+/hour in outage penalties under regulatory frameworks.
- **Safety:** Unplanned outages affecting hospitals, fire stations, and water treatment plants create direct public-safety risks.
- **Scale:** A utility managing 100 assets with current calendar-based maintenance likely performs 60% of its maintenance on assets that didn't need it, while under-servicing the 15% that are genuinely near failure.
- **Urgency:** Climate change is increasing the frequency and severity of weather events (heatwaves, storms) that stress grid equipment — making weather-correlated risk assessment more critical than ever.

## Why Existing Solutions Fall Short

| Current approach | Why it fails |
|---|---|
| Calendar-based maintenance (e.g., every 6 months) | Treats all assets equally — ignores real sensor trends; wastes crew time on healthy assets; misses accelerated degradation |
| Siloed SCADA dashboards | Show raw sensor values but provide no failure-probability score, no cross-asset risk ranking, and no weather overlay |
| Manual post-incident analysis | Reactive by nature — the failure has already happened; insights arrive too late to prevent the next one |
| Generic asset management software (SAP PM, IBM Maximo) | Schedule-driven, not predictive; do not ingest real-time sensor streams or correlate them with weather events |

GridGuard AI addresses every one of these gaps by fusing sensor telemetry, weather forecasts, and incident history into a single risk-ranked view that maintenance planners can act on *before* equipment fails.
