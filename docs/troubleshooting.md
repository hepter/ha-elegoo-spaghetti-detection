# Troubleshooting

## Setup Fails On ML Health

Use the ML server base URL, not a specific endpoint:

```text
http://192.168.1.100:3333
```

Do not enter:

```text
http://192.168.1.100:3333/hc/
http://192.168.1.100:3333/p/
```

Check:

```bash
curl "http://192.168.1.100:3333/hc/"
```

The browser dashboard is also useful:

```text
http://192.168.1.100:3333/
```

## Setup Fails On Camera Image Fetch

The ML server must be able to fetch the Home Assistant camera image URL.

Common cause:

```text
http://homeassistant.local:8123
```

works from a browser but not from a Docker container because mDNS is not
resolved there.

Use a LAN IP URL reachable by the ML server:

```text
http://192.168.1.90:8123
```

You can test only image fetch/decode without running the model:

```bash
curl --get "http://192.168.1.100:3333/debug/image" \
  --data-urlencode "img=http://192.168.1.90:8123/api/camera_proxy/camera.example?token=..." \
  --data-urlencode "token=obico_api_secret"
```

## Camera Entity Does Not Provide An Image

Some camera integrations expose stream-only entities or changed entity IDs after
updates. Set `Direct snapshot URL` if the selected camera has no `entity_picture`
attribute, or update the detector options after the camera entity ID changes.

## Multiple Detectors

Each config entry has a separate detector runtime and entity prefix. The Home
Assistant side supports multiple cameras.

The ML server is intentionally single-worker by default. The integration
serializes ML calls so multiple detectors do not hit the single worker at the
same instant. If you have a stronger host and many cameras, increase
`GUNICORN_WORKERS` carefully.

## CUDA Or Worker Timeout

The server defaults to CPU mode:

```text
ML_USE_GPU=false
GUNICORN_TIMEOUT=120
```

Only enable GPU when Docker has a working NVIDIA runtime. If you see CUDA driver
errors, keep GPU disabled.

## Detection Looks Too Quiet

Open the ML server dashboard:

```text
http://<server-ip>:3333/
```

Or check recent request logs:

```bash
curl "http://<server-ip>:3333/api/logs?token=obico_api_secret"
```

You can also press the `Test Spaghetti Detection` button in Home Assistant.

## Scheduled Detection Runs While Printer Is Idle

Scheduled detection is gated by `Print status sensor` unless
`Run scheduled detection without print status` is enabled.

Check these options first:

```text
Print status sensor: sensor.elegoo_centauri_carbon2_print_status
Active print states: printing
Run scheduled detection without print status: off
```

If the status sensor is `idle`, `complete`, `paused`, `unknown`, or
`unavailable`, the scheduled interval should wait and the detector status should
show `waiting_for_print` or `status_unavailable`.

For Elegoo-style entity names, a selected
`sensor.<printer>_print_status` automatically uses
`sensor.<printer>_current_status` as a second guard when that entity exists. If
`print_status` is `printing` but `current_status` is `idle`, `homing`, or
another non-active state, scheduled detection waits and `last_run` does not
advance.

The `Test Spaghetti Detection` button and the `run_detection` service with
`force: true` always run one manual check, even when the printer is not
printing.

## Notifications Repeat Every Interval

Notification, pause, and stop automations should trigger on:

```text
elegoo_spaghetti_detection_detected
```

Do not use this event for normal notifications:

```text
elegoo_spaghetti_detection_result
```

The result event fires after every completed detection check, including repeated
detected checks. The detected event is limited to one scheduled failure event
per active print window when a print status sensor is configured.
