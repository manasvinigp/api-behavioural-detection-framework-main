"""
Minimal gRPC test executor.

Provides a small adapter around generated protobuf Python stubs to execute unary
RPCs for demo/testing purposes. Not a full-featured integration — intended to be
used by test generators or demo runners to call methods and validate responses.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import grpc
from google.protobuf.json_format import ParseDict, MessageToDict


class GrpcTestExecutor:
    """Execute unary gRPC calls using generated Python stubs.

    Usage:
      executor = GrpcTestExecutor(target="localhost:50051", stub_path="demo/.../recommendationservice")
      executor.load_stubs()
      status, resp = executor.call_rpc(service_stub_name="RecommendationServiceStub", method_name="ListRecommendations", request_message_name="ListRecommendationsRequest", request_dict={...})
    """

    def __init__(self, target: str, stub_path: Optional[Path] = None, timeout: float = 5.0):
        self.target = target
        self.stub_path = Path(stub_path) if stub_path else None
        self.timeout = timeout
        self.pb2 = None
        self.pb2_grpc = None

    def load_stubs(self) -> None:
        """Dynamically import generated `*_pb2.py` and `*_pb2_grpc.py` from stub_path.

        stub_path should be the directory containing `demo_pb2.py` / `demo_pb2_grpc.py`.
        """
        if not self.stub_path:
            raise RuntimeError("stub_path must be provided to load generated proto stubs")

        # Insert stub path into sys.path temporarily
        p = str(self.stub_path.resolve())
        if p not in sys.path:
            sys.path.insert(0, p)

        try:
            import demo_pb2 as pb2  # type: ignore
            import demo_pb2_grpc as pb2_grpc  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to import generated proto stubs from {self.stub_path}: {e}")

        self.pb2 = pb2
        self.pb2_grpc = pb2_grpc

    def call_rpc(self, service_stub_name: str, method_name: str, request_message_name: str, request_dict: Dict[str, Any]) -> Tuple[grpc.StatusCode, Optional[Dict[str, Any]]]:
        """Call a unary RPC and return (status, response_dict).

        - `service_stub_name`: e.g., `RecommendationServiceStub` (class in demo_pb2_grpc)
        - `method_name`: e.g., `ListRecommendations`
        - `request_message_name`: e.g., `ListRecommendationsRequest` (class in demo_pb2)
        - `request_dict`: JSON-serializable dict representing the request
        """
        if not self.pb2 or not self.pb2_grpc:
            raise RuntimeError("Stubs not loaded; call load_stubs() first")

        # Get message and stub classes
        try:
            RequestCls = getattr(self.pb2, request_message_name)
        except AttributeError:
            raise RuntimeError(f"Request message {request_message_name} not found in pb2 module")

        try:
            StubCls = getattr(self.pb2_grpc, service_stub_name)
        except AttributeError:
            raise RuntimeError(f"Service stub {service_stub_name} not found in pb2_grpc module")

        # Build request proto
        req = RequestCls()
        try:
            ParseDict(request_dict, req)
        except Exception as e:
            raise RuntimeError(f"Failed to parse request dict into {request_message_name}: {e}")

        # Create channel and call
        with grpc.insecure_channel(self.target) as channel:
            stub = StubCls(channel)
            method = getattr(stub, method_name, None)
            if method is None:
                raise RuntimeError(f"Method {method_name} not found on stub {service_stub_name}")

            try:
                resp = method(req, timeout=self.timeout)
                resp_dict = MessageToDict(resp, preserving_proto_field_name=True)
                return (grpc.StatusCode.OK, resp_dict)
            except grpc.RpcError as e:
                # Map to status code and optional details
                code = e.code()
                details = None
                try:
                    # Some responses include details in trailing metadata; ignore for now
                    details = {"details": e.details()}
                except Exception:
                    details = None
                return (code, details)


# Simple wrapper for use by demo runners
def run_demo_call(target: str, stub_dir: str) -> None:
    exe = GrpcTestExecutor(target=target, stub_path=Path(stub_dir))
    exe.load_stubs()

    # Example call to RecommendationService.ListRecommendations
    req = {"user_id": "test-user", "products": []}
    status, resp = exe.call_rpc(
        service_stub_name="RecommendationServiceStub",
        method_name="ListRecommendations",
        request_message_name="ListRecommendationsRequest",
        request_dict=req,
    )

    print("gRPC call status:", status)
    print("response:", resp)
