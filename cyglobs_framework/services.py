"""Default request handlers."""


def echo_service(payload):
    return {"echo": payload.get("message", "")}


def compare_service(payload):
    a = payload.get("left")
    b = payload.get("right")
    return {"left": a, "right": b, "equal": a == b}


def health_service(payload):
    return {"service": "cyglobs", "healthy": True}
