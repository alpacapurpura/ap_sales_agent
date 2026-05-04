# Stories — scheduling

> SSoT atómico. 1 story = 1 archivo YAML.

## Stories activas

| ID | Type | Status | Capability | Last audit |
|----|------|--------|------------|------------|
| scheduling-google-availability-resolve | service-story | live | scheduling-google-calendar-sync | 2026-05-04 |
| scheduling-google-watch-channel-push | service-story | live | scheduling-google-calendar-sync | 2026-05-04 |
| scheduling-event-type-create | service-story | live | scheduling-event-types | 2026-05-04 |
| scheduling-event-type-public-link | service-story | live | scheduling-event-types | 2026-05-04 |
| scheduling-public-book-confirm-ics | service-story | live | scheduling-public-booking | 2026-05-04 |
| scheduling-cancel-reschedule | service-story | live | scheduling-public-booking | 2026-05-04 |

## Cómo agregar story nueva

1. `/po` skill toma user story
2. Crea `{story-id}.yaml` siguiendo template
3. Vincula a capability en `../capabilities/scheduling/{cap}.yaml`
4. /pm ratifica al merge → actualiza esta tabla
