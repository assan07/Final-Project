from flask import Flask, render_template, request, jsonify, url_for, flash, session, redirect
from pymongo import MongoClient
from jinja2 import Environment, FileSystemLoader
import os
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from bson import ObjectId
import secrets
from datetime import datetime, timedelta

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
app.secret_key = 'my_super_secret_key_12345'

bcrypt = Bcrypt(app)

# Direktori untuk menyimpan gambar
UPLOAD_FOLDER = 'static/images/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Fungsi untuk memeriksa apakah ekstensi file diperbolehkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
# Home dan halaman about
@app.route("/")
def home():
    if 'user_id' in session:
        full_name = session.get("full_name", "Guest")
        return render_template("main/index.html", full_name=full_name)
        # return render_template("main/index.html", full_name=session['full_name'])
    else:
        return redirect(url_for('user_login'))

# Rute untuk accounts/admin
# Rute untuk halaman data barang admin
@app.route("/accounts/admin/data_barang")
def admin_data_barang():
    barang_collection = db.barang
    barang_data = list(barang_collection.find())
    return render_template("accounts/admin/data_barang.html", barang_data=barang_data)

# Rute untuk menambah barang
@app.route("/accounts/admin/data_barang/tambah_barang", methods=["POST"])
def tambah_barang():
    kategori = request.form.get('kategori')
    brand = request.form.get('brand')
    netto = request.form.get('netto')
    warna = request.form.get('warna')
    harga = request.form.get('harga')
    stock = request.form.get('stock')

    # Mengambil foto produk
    foto = request.files.get('foto')
    foto_filename = None

    if foto and allowed_file(foto.filename):
        foto_filename = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

    # Menyimpan data ke MongoDB
    barang_collection = db.barang
    barang_collection.insert_one({
        "kategori": kategori,
        "brand": brand,
        "netto": netto,
        "warna": warna,
        "harga": harga,
        "stock": stock,
        "foto": foto_filename  # Simpan nama file gambar
    })

    return jsonify({"status": "success"}), 200

# Rute untuk delete barang
@app.route("/accounts/admin/data_barang/delete_barang", methods=["POST"])
def delete_barang():
    barang_id = request.form.get('id')
    barang_collection = db.barang

    # Cari barang berdasarkan ID
    barang = barang_collection.find_one({'_id': ObjectId(barang_id)})

    if barang:
        # Ambil nama file gambar
        foto_filename = barang.get('foto')
        if foto_filename:
            # Path lengkap file gambar
            foto_path = os.path.join(
                app.config['UPLOAD_FOLDER'], foto_filename)
            # Hapus file gambar jika ada
            if os.path.exists(foto_path):
                os.remove(foto_path)

        # Hapus data barang dari database
        result = barang_collection.delete_one({'_id': ObjectId(barang_id)})

        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Barang dan foto berhasil dihapus"}), 200
        else:
            return jsonify({"status": "error", "message": "Barang tidak ditemukan"}), 404
    else:
        return jsonify({"status": "error", "message": "Barang tidak ditemukan"}), 404

# Rute untuk edit barang
@app.route("/accounts/admin/data_barang/edit_barang", methods=["POST"])
def edit_barang():
    barang_id = request.form.get('id')
    kategori = request.form.get('kategori')
    brand = request.form.get('brand')
    netto = request.form.get('netto')
    warna = request.form.get('warna')
    harga = request.form.get('harga')
    stock = request.form.get('stock')
    foto = request.files.get('foto')
    foto_filename = None

    if foto and allowed_file(foto.filename):
        foto_filename = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

    barang_collection = db.barang
    update_data = {
        "kategori": kategori,
        "brand": brand,
        "netto": netto,
        "warna": warna,
        "harga": harga,
        "stock": stock,
    }
    if foto_filename:
        update_data["foto"] = foto_filename

    result = barang_collection.update_one({'_id': ObjectId(barang_id)}, {"$set": update_data})

    if result.modified_count > 0:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Barang tidak ditemukan atau tidak ada perubahan."}), 400

@app.route("/accounts/admin/data_user")
def admin_data_user():
    return render_template("accounts/admin/data_user.html")


@app.route("/accounts/admin/login_adm")
def admin_login():
    return render_template("accounts/admin/login_adm.html")

# Rute untuk accounts/users


@app.route("/accounts/users/login", methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')

        # Validasi input
        if not email or not password:
            flash('Email dan password harus diisi', 'error')
            return redirect(url_for('user_login'))

        # Cari user
        users_collection = db.user
        user = users_collection.find_one({'email': email})

        if user and bcrypt.check_password_hash(user['password'], password):
            # Login berhasil
            session['user_id'] = str(user['_id'])
            session['full_name'] = user['full_name']

            flash('Login berhasil!', 'success')
            # Redirect ke halaman dashboard
            return redirect(url_for('home'))
        else:
            flash('Email atau password salah', 'error')
            return redirect(url_for('user_login'))

    return render_template("accounts/users/login.html")


@app.route("/accounts/users/register", methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validasi input
        if not full_name or not email or not password:
            flash('Semua field harus diisi', 'error')
            return redirect(url_for('user_register'))

        # Cek apakah email sudah ada
        users_collection = db.user
        existing_user = users_collection.find_one({'email': email})

        if existing_user:
            flash('Email sudah terdaftar', 'error')
            return redirect(url_for('user_register'))

        # Hash password
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        # Simpan user baru
        users_collection.insert_one({
            'full_name': full_name,
            'email': email,
            'password': hashed_password
        })

        flash('Registrasi berhasil! Silakan login', 'success')
        return redirect(url_for('user_login'))

    return render_template("accounts/users/register.html")

# route untuk mencek apakah user sudah login atau blum

@app.route("/accounts/users/status", methods=["GET"])
def user_status():
    # Cek apakah ada sesi aktif
    if "user_id" in session:
        return jsonify({
            "is_logged_in": True,
            "full_name": session.get("full_name", "User")
        })
    else:
        return jsonify({
            "is_logged_in": False
        })

# route logout

@app.route("/accounts/users/logout", methods=["GET"])
def user_logout():
    # Hapus sesi user
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("home"))


@app.route("/accounts/users/reset-password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    reset_data = db.password_resets.find_one({
        'token': token,
        'expiry': {'$gt': datetime.utcnow()}
    })

    if not reset_data:
        flash('Link tidak valid atau sudah kadaluarsa', 'error')
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        new_password = bcrypt.generate_password_hash(
            request.form['password']).decode('utf-8')

        db.user.update_one(
            {'email': reset_data['email']},
            {'$set': {'password': new_password}}
        )

        db.password_resets.delete_one({'token': token})

        flash('Password berhasil diubah', 'success')
        return redirect(url_for('user_login'))

    return render_template('accounts/users/reset_password.html')


@app.route("/accounts/users/forget-password", methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form['email']
        user = db.user.find_one({'email': email})

        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=1)

            db.password_resets.insert_one({
                'email': email,
                'token': token,
                'expiry': expiry
            })

            reset_link = url_for('reset_password', token=token, _external=True)
            flash(f'Link reset password: {reset_link}', 'success')
            return redirect(url_for('user_login'))

        flash('Email tidak ditemukan', 'error')
    return render_template('accounts/users/forget_password.html')


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

# Rute untuk products


@app.route("/products/product_details")
def product_details():
    return render_template("products/product_details.html")


@app.route("/products/product_lists")
def product_lists():
    return render_template("products/product_lists.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
