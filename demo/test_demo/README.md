Demo Test Input (microservices-demo)
===================================

This folder is a testing workspace where you can import artifacts (OpenAPI specs, example traffic, mock services) from external projects such as GoogleCloudPlatform/microservices-demo and run `acv` against them.

Quick steps
-----------

1. Clone the microservices-demo into this folder (script provided):

   - Run `fetch_microservices_demo.bat` and follow prompts.

2. Prepare OpenAPI specs:

   - If the cloned repo includes OpenAPI specs, copy them into `demo\test_demo\openapi`.
   - Otherwise, create minimal OpenAPI YAML files for the services you want to test and place them in `demo\test_demo\openapi`.

3. Start the target services (microservices-demo) locally according to its README (Docker Compose or Kubernetes).

4. Run validation using the provided config (this points to the sample users API by default):

   ```bat
   .venv\Scripts\activate
   acv validate --config demo\test_demo\acv_config.yaml
   ```

5. Reports will be written to `demo\test_demo\reports`.

Notes
-----
- The `fetch_microservices_demo.bat` script requires `git` to be installed and in PATH.
- Generating accurate OpenAPI specs for every microservice may require inspecting the microservices' source code or adding API gateways/extraction tools.
- If you prefer, you can instead copy the single-service example spec `examples\openapi\sample_users_api.yaml` into `demo\test_demo\openapi` and run the demo against the included `examples\mock_apis\users_api.py`.

If you'd like, I can now run the clone script and attempt to auto-populate `demo\test_demo` (requires network access and git). Confirm and I'll proceed.
