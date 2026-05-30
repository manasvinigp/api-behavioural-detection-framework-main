# Shopping Assistant — Advanced PRD (Drift-inducing)

This advanced PRD intentionally specifies stricter/updated contract expectations to
exercise drift detection. It diverges from the running demo implementation on
purpose: required fields and response shape are different so validation should
detect drift when the runner merges PRD expectations.

POST /shoppingassistant

Request fields:

- message: string (required)
- user_intent: string (required)  # NEW required business-level field
- image: string (optional)
- user_id: string (optional, uuid)
- filters: object (optional)

Request rules:

- `user_intent` MUST be provided and must be one of: "browse", "buy", "compare".
- `message` must be non-empty and <= 500 characters.

Responses

200 (application/json)

Response body fields (schema):

- recommendations: array (required)
  - id: string (required)
  - title: string (required)  # NEW: title is required in advanced PRD
  - price: number (required)
  - currency: string (required)  # NEW: currency required
  - image_url: string|null
  - score: number (0..1)

- received: object (required)
  - message: string
  - image: string|null
  - user_id: string|null
  - user_intent: string

Error responses

- 400 validation_failed: when required fields missing or invalid types
- 422 semantic_error: when `user_intent` not in allowed set

Notes

- This PRD intentionally requires `user_intent`, `recommendations[].title`, and
  `recommendations[].currency` which the demo implementation does not provide.
  Running the PRD-driven validation with this file should yield detectable
  contract/validation drift.
