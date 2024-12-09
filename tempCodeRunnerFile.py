@app.route("/carts/order_summary/update-cart", methods=["POST"])
# def update_cart():
#     try:
#         data = request.json
#         item_id = data.get("item_id")
#         quantity = data.get("quantity", 1)

#         # Validasi input
#         if not item_id or not isinstance(quantity, int) or quantity < 1:
#             return jsonify({"message": "Invalid item_id or quantity"}), 400

#         # Konversi item_id ke ObjectId
#         item_id = ObjectId(item_id)

#         # Perbarui item di keranjang berdasarkan _id
#         result = db.cart.update_one({"_id": item_id}, {"$set": {"quantity": quantity}})

#         if result.matched_count == 0:
#             return jsonify({"message": "Item not found in cart"}), 404

#         # Ambil item yang diperbarui
#         updated_item = db.cart.find_one({"_id": item_id})

#         # Serialisasi ObjectId dan hitung ulang subtotal
#         serialized_item = serialize_object_id(updated_item)
#         updated_price = float(serialized_item["harga"]) * int(serialized_item["quantity"])

#         return jsonify({"message": "Quantity updated", "updated_price": updated_price}), 200

#     except Exception as e:
#         return jsonify({"message": f"An errort occurred: {str(e)}"}), 500