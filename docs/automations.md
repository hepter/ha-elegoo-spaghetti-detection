# Automation Examples

The integration only detects failures and emits entities/events. Printer actions
use your own Home Assistant entities directly.

Example Elegoo CC2 entities used by the templates:

```text
button.elegoo_centauri_carbon2_pause_print
button.elegoo_centauri_carbon2_resume_print
button.elegoo_centauri_carbon2_stop_print
camera.elegoo_centauri_carbon2_chamber_camera
sensor.elegoo_centauri_carbon2_print_status
```

Your entity IDs may differ if your printer/device name differs.

## Included Examples

- [Notify only](../examples/notify_only.yaml)
- [Actionable mobile notification with pause/stop/resume](../examples/actionable_notification.yaml)
- [Confidence-based pause/stop](../examples/smart_pause_stop_by_confidence.yaml)
- [Manual test notification](../examples/manual_test_notification.yaml)

## Event Data

Use `elegoo_spaghetti_detection_detected` for notifications and printer
actions. When a print status sensor is configured, scheduled detected events are
sent once per active print window to avoid repeated pause/notify loops. Use
`elegoo_spaghetti_detection_result` only when you intentionally want every
detection result, including clear and warning checks.

These two events are intentionally different:

| Event | When it fires | Use for notifications/actions? |
| --- | --- | --- |
| `elegoo_spaghetti_detection_detected` | Only when a failure is detected and the active print window has not already emitted one detected event. | Yes. Use this for Pushbullet, mobile notifications, pause, and stop automations. |
| `elegoo_spaghetti_detection_result` | Every completed detection check, including clear, warning, and repeated detected checks. | Usually no. Use it only for logging, dashboards, or advanced automations that implement their own throttling. |

If an automation sends notifications from
`elegoo_spaghetti_detection_result`, it can still notify repeatedly every
detection interval. The included notification and pause/stop examples use
`elegoo_spaghetti_detection_detected` to avoid that.

Use these fields in templates:

```text
trigger.event.data.confidence
trigger.event.data.raw_score
trigger.event.data.detected
trigger.event.data.detections
trigger.event.data.image_url
trigger.event.data.printer_state
trigger.event.data.status
trigger.event.data.last_error
```

Confidence is a number between `0` and `1`. For notification text:

```jinja
{{ (trigger.event.data.confidence | float(0) * 100) | round(1) }}%
```

The `image_url` field is the exact camera snapshot URL the ML server checked.
Mobile notifications can use it as an image attachment. If your phone is away
from the LAN, make sure the `Home Assistant Host` you configured is reachable
from that phone, or use a notification-only message without the image.
