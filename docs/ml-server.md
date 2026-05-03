# ML Server And Logs

The ML server listens on port `3333` and exposes the Obico/TSD model used for
failure detection.

## Standalone Docker Compose

```bash
git clone https://github.com/hepter/ha-elegoo-spaghetti-detection.git
cd ha-elegoo-spaghetti-detection
docker compose up -d
```

Default URL:

```text
http://<server-ip>:3333
```

Default token:

```text
obico_api_secret
```

Change `ML_API_TOKEN` before exposing this service outside a trusted local
network.

## Runtime Endpoints

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `/` | no | Small browser status page and recent redacted requests. |
| `/hc/` | no | Health check, returns `ok`. |
| `/api/status` | no | JSON status, model backend, threshold, request count. |
| `/api/logs?token=<token>` | yes | Recent request logs. Image query tokens are not shown in the dashboard. |
| `/debug/image?img=<url>&token=<token>` | yes | Fetch and decode a camera image without running inference. Used by setup validation. |
| `/p/?img=<url>` | yes | Prediction endpoint used by Home Assistant. |

The token can be passed as either:

```text
Authorization: Bearer <token>
```

or, for browser debugging only:

```text
?token=<token>
```

## CPU/GPU Behavior

The server is CPU-first by default:

```text
ML_USE_GPU=false
ML_MODEL_BACKEND=onnx
GUNICORN_TIMEOUT=120
GUNICORN_WORKERS=1
```

This avoids slow CUDA probing and gunicorn worker timeouts on machines without a
working NVIDIA runtime. Enable GPU only when Docker has working NVIDIA support:

```text
ML_USE_GPU=true
```

## Logs

Docker:

```bash
docker logs -f ha_elegoo_spaghetti_detection
```

Recent in-app request log:

```bash
curl "http://<server-ip>:3333/api/logs?token=obico_api_secret"
```

Health and model backend:

```bash
curl "http://<server-ip>:3333/api/status"
```

When testing a camera URL by hand, URL-encode the image URL:

```bash
curl --get "http://<server-ip>:3333/debug/image" \
  --data-urlencode "img=http://homeassistant.local:8123/api/camera_proxy/camera.example?token=..." \
  --data-urlencode "token=obico_api_secret"
```
