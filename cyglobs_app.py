from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import parse, request
from uuid import uuid4

from ai_generation import generate_image, provider_features
from cyglobs_framework.comparators import ProtocolComparator
from cyglobs_framework.config import ServerConfig
from cyglobs_framework.contingency import FallbackPlanner
from cyglobs_framework.inverse_ops import InverseOperatorRegistry
from cyglobs_framework.protocol import RequestEnvelope, ResponseEnvelope
from cyglobs_framework.services import compare_service, echo_service, health_service
from graphics_runtime import DEFAULT_RADIUS, Directive, DirectivePacket, Opcode

ROOT = Path(__file__).resolve().parent
STORAGE = Path(os.getenv("DISCRETE_STORAGE_DIR", ROOT / "storage")).resolve()
DATABASE = Path(os.getenv("DISCRETE_DATABASE_PATH", ROOT / "discrete_art_studio.db")).resolve()
SECRET_KEY = os.getenv("DISCRETE_SECRET_KEY", "development-only-change-me").encode()
STRIPE_SECRET_KEY = os.getenv("DISCRETE_STRIPE_SECRET_KEY", "")
STARTING_CREDITS = int(os.getenv("DISCRETE_STARTING_CREDITS", "20"))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

STORAGE.mkdir(parents=True, exist_ok=True)
config = ServerConfig()
comparator = ProtocolComparator(config.protocol_version)
fallbacks = FallbackPlanner()
operations = InverseOperatorRegistry()
operations.register("echo", echo_service)
operations.register("compare", compare_service)
operations.register("health", health_service)


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                credits INTEGER NOT NULL DEFAULT 20,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS creations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                style TEXT NOT NULL,
                mode TEXT NOT NULL,
                image_url TEXT NOT NULL DEFAULT '',
                likes INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );
            """
        )


def password_digest(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    raw = base64.urlsafe_b64decode(encoded.encode())
    salt, expected = raw[:16], raw[16:]
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return hmac.compare_digest(actual, expected)


def issue_token(user_id: int, ttl_seconds: int = 86_400) -> str:
    payload = f"{user_id}:{int(time.time()) + ttl_seconds}".encode()
    signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload + b"." + signature).decode()


def decode_token(token: str) -> int:
    raw = base64.urlsafe_b64decode(token.encode())
    payload, signature = raw.rsplit(b".", 1)
    expected = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid token signature")
    user_id_text, expiry_text = payload.decode().split(":", 1)
    if int(expiry_text) < int(time.time()):
        raise ValueError("token expired")
    return int(user_id_text)


def provider_generate(prompt: str, style: str, mode: str) -> str:
    result = generate_image(
        {
            "prompt": prompt,
            "style": style,
            "mode": mode,
            "aspect_ratio": "1:1",
            "quality": "medium",
            "output_format": "png",
        },
        STORAGE,
    )
    return result.image_url


def generate_image_service(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_image(payload, STORAGE).to_dict()


def feature_requirements_service(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime": "embedded CyGlobs Python framework",
        "renderer": "CyGlobsGL",
        "generation": provider_features(),
        "requirements": [
            "Python 3.11+",
            "configured image provider credentials for real AI output",
            "writable local storage directory",
            "CyGlobsGL local fallback",
        ],
    }


def render_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt", "")).strip()
    if len(prompt) < 3:
        raise ValueError("prompt is too short")
    mode = str(payload.get("mode", "Wireframe"))
    if mode not in {"Wireframe", "Triangles", "Contingency"}:
        raise ValueError("unknown render mode")
    rotation = float(payload.get("rotation", 0.0))
    packet = DirectivePacket(
        Directive(Opcode.ROTATE, 7, rotation, DEFAULT_RADIUS, 0.0)
    )
    return {
        "renderer": "CyGlobsGL",
        "prompt": prompt,
        "style": str(payload.get("style", "Cinematic")),
        "mode": mode,
        "radius": DEFAULT_RADIUS,
        "directive_packet": packet.to_hex(),
        "pipeline": [
            "Sort/Jecht",
            "Translate/Daq",
            "Rotate/MVP",
            "Scale/Cap",
            "Clip Space",
            "Framebuffer",
        ],
    }


operations.register("render_manifest", render_manifest)
operations.register("generate_image", generate_image_service)
operations.register("feature_requirements", feature_requirements_service)


class DiscreteHandler(SimpleHTTPRequestHandler):
    server_version = "DiscreteCyGlobs/1.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_UPLOAD_BYTES * 2:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length) if length else b"{}"
        value = json.loads(raw.decode())
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def _send_json(self, status: int, value: Any) -> None:
        raw = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _bearer_user_id(self) -> int:
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise PermissionError("missing bearer token")
        return decode_token(authorization[7:].strip())

    def do_GET(self) -> None:
        path = parse.urlparse(self.path).path
        if path == "/api/health":
            features = provider_features()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "runtime": "CyGlobs Python standard-library server",
                    "renderer": "CyGlobsGL",
                    "database": "sqlite3",
                    "provider_configured": features["real_ai_generation"],
                    "image_provider": features["provider"],
                },
            )
            return
        if path == "/api/features":
            self._send_json(HTTPStatus.OK, feature_requirements_service({}))
            return
        if path == "/api/creations":
            with connect_db() as db:
                rows = db.execute(
                    "SELECT id, owner_id, prompt, style, mode, image_url, likes, created_at "
                    "FROM creations ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
            self._send_json(HTTPStatus.OK, [dict(row) for row in rows])
            return
        if path == "/api/me":
            try:
                user_id = self._bearer_user_id()
                with connect_db() as db:
                    row = db.execute(
                        "SELECT id, email, display_name, credits FROM users WHERE id = ?",
                        (user_id,),
                    ).fetchone()
                if row is None:
                    raise PermissionError("user not found")
                self._send_json(HTTPStatus.OK, dict(row))
            except Exception as error:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": str(error)})
            return
        if path.startswith("/storage/"):
            candidate = (STORAGE / path.removeprefix("/storage/")).resolve()
            if STORAGE not in candidate.parents or not candidate.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            data = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = parse.urlparse(self.path).path
        try:
            body = self._json_body()
            if path == "/rpc":
                envelope = RequestEnvelope.from_dict(body)
                check = comparator.compare_version(envelope.protocol_version)
                if not check.passed:
                    response = ResponseEnvelope(status="error", error=check.reason)
                else:
                    response = ResponseEnvelope(
                        status="ok",
                        result=operations.execute(envelope.operation, envelope.payload),
                    )
                self._send_json(HTTPStatus.OK, response.to_dict())
                return
            if path == "/api/generate":
                self._send_json(
                    HTTPStatus.CREATED,
                    generate_image_service(body),
                )
                return
            if path == "/api/auth/register":
                email = str(body.get("email", "")).strip().lower()
                password = str(body.get("password", ""))
                display_name = str(body.get("display_name", "")).strip()[:80]
                if "@" not in email or len(password) < 8 or not display_name:
                    raise ValueError("valid email, display name, and 8-character password are required")
                with connect_db() as db:
                    try:
                        cursor = db.execute(
                            "INSERT INTO users(email, password_hash, display_name, credits, created_at) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (email, password_digest(password), display_name, STARTING_CREDITS, int(time.time())),
                        )
                        user_id = int(cursor.lastrowid)
                    except sqlite3.IntegrityError as error:
                        raise ValueError("email is already registered") from error
                self._send_json(HTTPStatus.CREATED, {"access_token": issue_token(user_id), "token_type": "bearer"})
                return
            if path == "/api/auth/token":
                email = str(body.get("email", body.get("username", ""))).strip().lower()
                password = str(body.get("password", ""))
                with connect_db() as db:
                    row = db.execute(
                        "SELECT id, password_hash FROM users WHERE email = ?", (email,)
                    ).fetchone()
                if row is None or not verify_password(password, row["password_hash"]):
                    raise PermissionError("incorrect email or password")
                self._send_json(HTTPStatus.OK, {"access_token": issue_token(row["id"]), "token_type": "bearer"})
                return
            if path == "/api/creations":
                user_id = self._bearer_user_id()
                prompt = str(body.get("prompt", "")).strip()
                style = str(body.get("style", "Cinematic"))
                mode = str(body.get("mode", "Wireframe"))
                if len(prompt) < 3:
                    raise ValueError("prompt is too short")
                with connect_db() as db:
                    user = db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
                    if user is None:
                        raise PermissionError("user not found")
                    if user["credits"] < 1:
                        self._send_json(HTTPStatus.PAYMENT_REQUIRED, {"error": "not enough credits"})
                        return
                    image_url = provider_generate(prompt, style, mode)
                    cursor = db.execute(
                        "INSERT INTO creations(owner_id, prompt, style, mode, image_url, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, prompt, style, mode, image_url, int(time.time())),
                    )
                    db.execute("UPDATE users SET credits = credits - 1 WHERE id = ?", (user_id,))
                    creation_id = int(cursor.lastrowid)
                self._send_json(HTTPStatus.CREATED, {"id": creation_id, "image_url": image_url})
                return
            if path.startswith("/api/creations/") and path.endswith("/like"):
                creation_id = int(path.split("/")[3])
                with connect_db() as db:
                    cursor = db.execute(
                        "UPDATE creations SET likes = likes + 1 WHERE id = ?", (creation_id,)
                    )
                    if cursor.rowcount == 0:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "creation not found"})
                        return
                    likes = db.execute("SELECT likes FROM creations WHERE id = ?", (creation_id,)).fetchone()["likes"]
                self._send_json(HTTPStatus.OK, {"id": creation_id, "likes": likes})
                return
            if path == "/api/uploads":
                user_id = self._bearer_user_id()
                filename = Path(str(body.get("filename", "upload.bin"))).name
                suffix = Path(filename).suffix.lower()
                if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                    raise ValueError("unsupported image type")
                contents = base64.b64decode(str(body.get("data_base64", "")), validate=True)
                if len(contents) > MAX_UPLOAD_BYTES:
                    self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "file exceeds 10 MB"})
                    return
                target = STORAGE / f"{user_id}-{uuid4().hex}{suffix}"
                target.write_bytes(contents)
                self._send_json(HTTPStatus.CREATED, {"url": f"/storage/{target.name}"})
                return
            if path == "/api/billing/checkout":
                user_id = self._bearer_user_id()
                if not STRIPE_SECRET_KEY:
                    self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Stripe is not configured"})
                    return
                form = parse.urlencode(
                    {
                        "mode": "payment",
                        "success_url": "http://127.0.0.1:8000/?payment=success",
                        "cancel_url": "http://127.0.0.1:8000/?payment=cancelled",
                        "line_items[0][price_data][currency]": "usd",
                        "line_items[0][price_data][product_data][name]": "100 Discrete credits",
                        "line_items[0][price_data][unit_amount]": "999",
                        "line_items[0][quantity]": "1",
                        "metadata[user_id]": str(user_id),
                    }
                ).encode()
                req = request.Request(
                    "https://api.stripe.com/v1/checkout/sessions",
                    data=form,
                    headers={
                        "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    method="POST",
                )
                with request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode())
                self._send_json(HTTPStatus.OK, {"checkout_url": result.get("url", "")})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "endpoint not found"})
        except PermissionError as error:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": str(error)})
        except Exception as error:
            fallback = fallbacks.fallback_response(error)
            self._send_json(HTTPStatus.BAD_REQUEST, fallback)


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    initialize_database()
    return ThreadingHTTPServer((host or config.host, port or config.port), DiscreteHandler)


def main() -> None:
    server = create_server()
    print(f"Discrete Art Studio running at http://{config.host}:{config.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
