@app.route("/carts/order_history")
# def order_history():
#     if "user_id" in session:
#         # Ambil informasi pengguna
#         user_id = session["user_id"]
#         email = session.get("email", "Tidak ada email")
#         full_name = session.get("full_name", "Guest")

#         # Ambil koleksi pesanan
#         orders_collection = db.orders

#         # Ambil data pesanan berdasarkan user_id
#         order_items = list(orders_collection.find({"user_id": user_id}))

#         # Render template dengan data pesanan
#         return render_template("carts/order_history.html", 
#                                full_name=full_name, 
#                                email=email, 
#                                order_items=order_items)
#     else:
#         return redirect(url_for('user_login'))
    