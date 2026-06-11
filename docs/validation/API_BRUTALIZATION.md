# API Brutalization

## Intent
Defend the FastAPI ingress layer against malicious, malformed, or absurd client requests.

## Brutalization Script
`backend/scripts/test_api_brutalization.py` invokes the FastAPI ASGI app directly (bypassing TCP) using `httpx.AsyncClient`.

### Attack Vectors Validated
- `limit=999999999999`: Ensures Pydantic `<Field(le=100)>` correctly triggers `422 Unprocessable Entity` rather than locking the DB cursor.
- `limit=-5`: Ensures `ge=1` triggers `422`.
- `q='; DROP TABLE articles;--`: Ensures parameterized SQL (`to_tsquery`) correctly sanitizes the input as a literal string.
- `cursor=invalid-base64`: Ensures graceful failure on pagination decode.

## Expected Behavior
The API must return `HTTP 422` with a detailed `detail` JSON body explaining the Pydantic type coercion failure. It must NEVER return `HTTP 500` or drop connection for these requests.

## Failure Interpretation
An HTTP 500 implies that Pydantic validation was bypassed or the Router manually attempted to parse an untrusted variable before SQLAlchemy parameterization.
