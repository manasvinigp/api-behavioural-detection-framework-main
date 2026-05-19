from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/shoppingassistant', methods=['POST'])
def shopping_assistant():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid_json", "message": "Request body must be a JSON object"}), 400

    # Basic validation to satisfy OpenAPI constraints
    # Required: message (string)
    message = data.get("message")
    image = data.get("image") if "image" in data else None

    errors = []
    if message is None:
        errors.append({"field": "message", "error": "missing_required", "expected": "string"})
    elif not isinstance(message, str):
        errors.append({"field": "message", "error": "invalid_type", "expected": "string"})

    if image is not None and not isinstance(image, str):
        errors.append({"field": "image", "error": "invalid_type", "expected": "string"})

    if errors:
        return jsonify({"error": "validation_failed", "details": errors}), 400

    # Ensure consistent response structure: always include 'received.image' key (null if absent)
    received = {"message": message, "image": image}

    return jsonify({
        "recommendations": [
            {"product_id": "1", "score": 0.9},
            {"product_id": "2", "score": 0.75}
        ],
        "received": received
    })


@app.route('/product/<product_id>', methods=['GET'])
def product(product_id):
    return jsonify({
        "id": product_id,
        "name": f"Product {product_id}",
        "price": 9.99
    })


@app.route('/product-meta/<ids>', methods=['GET'])
def product_meta(ids):
    id_list = ids.split(',')
    meta = [{"id": i, "stock": 10, "meta": {}} for i in id_list]
    return jsonify({"products": meta})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
