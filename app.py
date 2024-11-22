from flask import Flask, render_template

import os

app = Flask(__name__, template_folder=os.path.join('app', 'templates'))

# Home dan halaman about
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# Rute untuk accounts/admin
@app.route("/accounts/admin/data_barang")
def admin_data_barang():
    return render_template("accounts/admin/data_barang.html")

@app.route("/accounts/admin/data_user")
def admin_data_user():
    return render_template("accounts/admin/data_user.html")

# Rute untuk accounts/users
@app.route("/accounts/users/login")
def user_login():
    return render_template("accounts/users/login.html")

@app.route("/accounts/users/register")
def user_register():
    return render_template("accounts/users/register.html")

@app.route("/accounts/users/profile")
def user_profile():
    return render_template("accounts/users/profile.html")

@app.route("/accounts/users/edit_password")
def edit_password():
    return render_template("accounts/users/edit_password.html")

# Rute untuk carts
@app.route("/carts/order_history")
def order_history():
    return render_template("carts/order_history.html")

@app.route("/carts/order_summary")
def order_summary():
    return render_template("carts/order_summary.html")

@app.route("/carts/payment")
def payment():
    return render_template("carts/payment.html")

# Rute untuk products
@app.route("/products/collections")
def collections():
    return render_template("products/collections.html")

@app.route("/products/product_details")
def product_details():
    return render_template("products/product_details.html")

@app.route("/products/product_lists")
def product_lists():
    return render_template("products/product_lists.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

