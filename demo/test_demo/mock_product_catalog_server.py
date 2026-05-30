#!/usr/bin/env python3
"""Minimal mock ProductCatalog gRPC server for local demo runs.

Starts a gRPC server implementing ProductCatalogService.ListProducts and
returns products from the productcatalogservice/products.json file.
"""
import json
import sys
from pathlib import Path
import os
import time
from concurrent import futures

# ensure we can import generated protos from the recommendationservice folder
_this_dir = Path(__file__).resolve().parent
_stub_dir = (_this_dir / "microservices-demo" / "src" / "recommendationservice").resolve()
if str(_stub_dir) not in sys.path:
    sys.path.insert(0, str(_stub_dir))

import demo_pb2
import demo_pb2_grpc
import grpc

PRODUCTS_JSON = _this_dir / "microservices-demo" / "src" / "productcatalogservice" / "products.json"

class ProductCatalogServicer(demo_pb2_grpc.ProductCatalogServiceServicer):
    def __init__(self, products):
        self.products = products

    def ListProducts(self, request, context):
        resp = demo_pb2.ListProductsResponse()
        for p in self.products:
            prod = demo_pb2.Product()
            prod.id = p.get("id", "")
            prod.name = p.get("name", "")
            prod.description = p.get("description", "")
            prod.picture = p.get("picture", "")
            price = p.get("priceUsd", {})
            money = demo_pb2.Money()
            money.currency_code = price.get("currencyCode", "USD")
            money.units = int(price.get("units", 0))
            money.nanos = int(price.get("nanos", 0))
            prod.price_usd.CopyFrom(money)
            prod.categories.extend(p.get("categories", []))
            resp.products.append(prod)
        return resp


def serve(host="127.0.0.1", port=3560):
    if not PRODUCTS_JSON.exists():
        raise RuntimeError(f"products.json not found at {PRODUCTS_JSON}")
    data = json.loads(PRODUCTS_JSON.read_text())
    products = data.get("products", [])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    demo_pb2_grpc.add_ProductCatalogServiceServicer_to_server(ProductCatalogServicer(products), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"Mock ProductCatalogService listening on {host}:{port}, {len(products)} products")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
