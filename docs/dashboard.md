# Dashboard Examples

These examples create a small Home Assistant dashboard section for one
spaghetti detector.

Replace entity IDs if your detector prefix, camera, printer, or automation names
are different. The examples use:

```text
camera.elegoo_centauri_carbon2_chamber_camera
sensor.elegoo_centauri_carbon2_print_status
sensor.elegoo_spaghetti_detection_status
sensor.elegoo_spaghetti_detection_next_run
sensor.elegoo_spaghetti_detection_last_run
sensor.elegoo_spaghetti_detection_last_error
sensor.elegoo_spaghetti_detection_confidence
sensor.elegoo_spaghetti_detection_raw_score
sensor.elegoo_spaghetti_detection_detections
binary_sensor.elegoo_spaghetti_detection_spaghetti_detected
button.elegoo_spaghetti_detection_test_spaghetti_detection
button.elegoo_spaghetti_detection_reset_detection_state
```

The enhanced example also references this placeholder automation:

```text
automation.elegoo_cc2_spaghetti_pause_and_notify
```

Replace it with your own notification or pause automation entity.
The toggle card in `dashboard_hacs.yaml` is only a placeholder until you make
that replacement.

## Status Labels

The dashboard examples render raw detector states as user-facing English labels:

| Raw state | Dashboard label |
| --- | --- |
| `clear` | Clear |
| `detected` | Failure detected |
| `warning` | Warning |
| `checking` | Checking |
| `waiting_for_print` | Waiting for print |
| `status_unavailable` | Print status unavailable |
| `busy` | Busy |
| `error` | Error |
| `idle` | Idle |

This avoids a mixed display where Home Assistant shows an unknown printer state
while the detector correctly reports `waiting_for_print`.

## Core Home Assistant Example

Use this when you do not want extra Lovelace dependencies:

- [examples/dashboard_core.yaml](../examples/dashboard_core.yaml)

It uses only built-in cards:

- `picture-entity`
- `markdown`
- `gauge`
- `conditional`
- `button`
- `entities`

## Enhanced HACS Example

Use this when custom Lovelace cards are allowed:

- [examples/dashboard_hacs.yaml](../examples/dashboard_hacs.yaml)

Idle state:

![Enhanced dashboard idle state](images/dashboard-hacs-waiting-for-print.png)

Detected failure state:

![Enhanced dashboard detected failure](images/dashboard-hacs-detected.png)

Recommended custom cards:

- `custom:button-card`
- `custom:mushroom-template-card`
- `card_mod`

Install those through HACS before pasting the enhanced YAML. The enhanced
version adds a compact status panel, better visual states, responsive metric
tiles, and an alert card when spaghetti is detected.

## Next Scheduled Check

The integration exposes:

```text
sensor.<prefix>_next_run
```

For the default prefix this is:

```text
sensor.elegoo_spaghetti_detection_next_run
```

The value is updated when the integration starts and every time the scheduled
interval fires. It represents the next scheduled interval tick. If the print
status is not active, the detector still waits at that tick and keeps the status
as `waiting_for_print`.
