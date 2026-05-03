#!/usr/bin/env python
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import logging
from os import environ, path
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit

import cv2
import flask
from flask import Response, jsonify, request
import numpy as np
import requests

from auth import token_required
from lib.detection_model import detect, load_net

THRESH = float(environ.get("ML_DETECTION_BOX_THRESHOLD", "0.08"))
REQUEST_TIMEOUT = (
    float(environ.get("ML_IMAGE_CONNECT_TIMEOUT", "2")),
    float(environ.get("ML_IMAGE_READ_TIMEOUT", "10")),
)
MAX_RECENT_REQUESTS = int(environ.get("ML_RECENT_REQUESTS", "100"))

app = flask.Flask(__name__)
app.config["DEBUG"] = environ.get("DEBUG") == "True"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
app.logger.setLevel(logging.INFO)

STARTED_AT = datetime.now(timezone.utc)
RECENT_REQUESTS: deque[dict] = deque(maxlen=MAX_RECENT_REQUESTS)

model_dir = path.join(path.dirname(path.realpath(__file__)), "model")
net_main = load_net(path.join(model_dir, "model.cfg"), path.join(model_dir, "model.meta"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    parsed = urlsplit(raw_url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _record_request(entry: dict) -> None:
    stored_entry = dict(entry)
    if "image_url" in stored_entry:
        stored_entry["image_url"] = _redact_url(stored_entry.get("image_url"))
    RECENT_REQUESTS.appendleft({"time": _now_iso(), **stored_entry})
    app.logger.info(
        "prediction status=%s detections=%s duration_ms=%s image_host=%s error=%s",
        entry.get("status"),
        entry.get("detections", 0),
        entry.get("duration_ms"),
        urlsplit(entry.get("image_url") or "").netloc,
        entry.get("error"),
    )


def _fetch_image(image_url: str) -> np.ndarray:
    response = requests.get(image_url, stream=True, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    img_array = np.array(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(img_array, -1)
    if image is None:
        raise ValueError("image_decode_failed")
    return image


def _status_payload() -> dict:
    return {
        "ok": net_main is not None,
        "started_at": STARTED_AT.isoformat(),
        "model": {
            "classes": ["failure"],
            "box_threshold": THRESH,
            "backend": type(net_main).__name__ if net_main is not None else None,
            "use_gpu": environ.get("ML_USE_GPU", "false"),
            "model_backend_preference": environ.get("ML_MODEL_BACKEND", "onnx"),
        },
        "requests": {
            "recent_count": len(RECENT_REQUESTS),
            "max_recent": MAX_RECENT_REQUESTS,
        },
    }


@app.route("/", methods=["GET"])
def dashboard():
    """Render a small operational status page."""
    status = _status_payload()
    rows = "\n".join(
        "<tr>"
        f"<td>{entry['time']}</td>"
        f"<td>{entry.get('status', '')}</td>"
        f"<td>{entry.get('detections', 0)}</td>"
        f"<td>{entry.get('duration_ms', '')}</td>"
        f"<td>{entry.get('error') or ''}</td>"
        f"<td>{_redact_url(entry.get('image_url')) or ''}</td>"
        "</tr>"
        for entry in list(RECENT_REQUESTS)[:20]
    )
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Elegoo Spaghetti Detection ML Server</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1f2933; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #d9e2ec; padding: 8px; text-align: left; font-size: 14px; }}
    .ok {{ color: #137333; font-weight: 700; }}
    .bad {{ color: #b3261e; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Elegoo Spaghetti Detection ML Server</h1>
  <p>Status: <span class="{'ok' if status['ok'] else 'bad'}">{'ok' if status['ok'] else 'error'}</span></p>
  <p>Backend: <code>{status['model']['backend']}</code> | GPU opt-in: <code>{status['model']['use_gpu']}</code> | Box threshold: <code>{status['model']['box_threshold']}</code></p>
  <p>Health: <code>/hc/</code> | JSON status: <code>/api/status</code> | Token-protected logs: <code>/api/logs?token=&lt;token&gt;</code></p>
  <h2>Recent Requests</h2>
  <table>
    <thead><tr><th>Time</th><th>Status</th><th>Detections</th><th>ms</th><th>Error</th><th>Image URL without token</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""
    return Response(body, mimetype="text/html")


@app.route("/api/status", methods=["GET"])
def api_status():
    """Return JSON server status."""
    return jsonify(_status_payload())


@app.route("/api/logs", methods=["GET"])
@token_required
def api_logs():
    """Return recent request logs."""
    return jsonify({"requests": list(RECENT_REQUESTS)})


@app.route("/debug/image", methods=["GET"])
@token_required
def debug_image():
    """Check whether the server can fetch and decode an image URL."""
    image_url = request.args.get("img")
    if not image_url:
        return jsonify({"ok": False, "error": "missing_image_url"}), 400
    started = perf_counter()
    try:
        image = _fetch_image(image_url)
        return jsonify(
            {
                "ok": True,
                "duration_ms": round((perf_counter() - started) * 1000),
                "shape": list(image.shape),
                "image_url": _redact_url(image_url),
            }
        )
    except requests.RequestException as err:
        return jsonify({"ok": False, "error": "image_fetch_failed", "message": str(err)}), 502
    except ValueError as err:
        return jsonify({"ok": False, "error": str(err)}), 422


@app.route("/p/", methods=["GET"])
@token_required
def get_p():
    """Run prediction for the image URL in the img query parameter."""
    image_url = request.args.get("img")
    if not image_url:
        _record_request({"status": 400, "error": "missing_image_url", "detections": 0})
        return jsonify(
            {
                "detections": [],
                "error": "missing_image_url",
                "message": "Missing img query parameter.",
            }
        ), 400

    started = perf_counter()
    try:
        image = _fetch_image(image_url)
        detections = detect(net_main, image, thresh=THRESH)
        duration_ms = round((perf_counter() - started) * 1000)
        _record_request(
            {
                "status": 200,
                "detections": len(detections),
                "duration_ms": duration_ms,
                "image_url": image_url,
            }
        )
        return jsonify({"detections": detections, "duration_ms": duration_ms})
    except requests.RequestException as err:
        duration_ms = round((perf_counter() - started) * 1000)
        _record_request(
            {
                "status": 502,
                "error": "image_fetch_failed",
                "message": str(err),
                "duration_ms": duration_ms,
                "image_url": image_url,
                "detections": 0,
            }
        )
        return jsonify(
            {
                "detections": [],
                "error": "image_fetch_failed",
                "message": str(err),
            }
        ), 502
    except ValueError as err:
        duration_ms = round((perf_counter() - started) * 1000)
        _record_request(
            {
                "status": 422,
                "error": str(err),
                "duration_ms": duration_ms,
                "image_url": image_url,
                "detections": 0,
            }
        )
        return jsonify(
            {
                "detections": [],
                "error": str(err),
                "message": "The image URL did not return a decodable image.",
            }
        ), 422
    except Exception as err:
        duration_ms = round((perf_counter() - started) * 1000)
        app.logger.exception("Unable to process image")
        _record_request(
            {
                "status": 500,
                "error": "prediction_failed",
                "message": str(err),
                "duration_ms": duration_ms,
                "image_url": image_url,
                "detections": 0,
            }
        )
        return jsonify(
            {
                "detections": [],
                "error": "prediction_failed",
                "message": str(err),
            }
        ), 500


@app.route("/hc/", methods=["GET"])
def health_check():
    """Health check for Home Assistant and Docker."""
    if net_main is not None:
        return "ok", 200
    return "error", 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, threaded=False)
