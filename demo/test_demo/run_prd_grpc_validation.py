"""
Demo runner that uses `GrpcTestExecutor` to call gRPC methods defined in
`demo/test_demo/microservices-demo/src/recommendationservice` generated stubs.

Run with:
  .\.venv\Scripts\python.exe demo/test_demo/run_prd_grpc_validation.py

This is a minimal demo to show PRD-driven gRPC calls; integrating with the full
`api_contract_validator` pipeline (test generation, drift detection) is a
follow-up task.
"""
from pathlib import Path

import sys
from pathlib import Path as _P

# Ensure repo `src/` is importable as a top-level package during demos
_src = str((_P(__file__).resolve().parents[2] / "src").resolve())
if _src not in sys.path:
    sys.path.insert(0, _src)

from api_contract_validator.execution.grpc_executor import GrpcTestExecutor  # type: ignore


def main():
    # Path to generated stubs (contains demo_pb2.py, demo_pb2_grpc.py)
    stub_dir = Path("demo/test_demo/microservices-demo/src/recommendationservice")

    target = "localhost:3550"  # default demo microservices gRPC port (adjust if needed)

    exe = GrpcTestExecutor(target=target, stub_path=stub_dir)
    try:
        exe.load_stubs()
    except Exception as e:
        print("Failed to load proto stubs:", e)
        return

    # Example request according to demo proto: ListRecommendationsRequest
    # Field names must match the protobuf JSON names (userId, productIds)
    request = {"userId": "test-user", "productIds": []}

    status, resp = exe.call_rpc(
        service_stub_name="RecommendationServiceStub",
        method_name="ListRecommendations",
        request_message_name="ListRecommendationsRequest",
        request_dict=request,
    )

    print("Status:", status)
    print("Response:", resp)


if __name__ == "__main__":
    main()
