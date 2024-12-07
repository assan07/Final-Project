from flask import Flask, render_template, request, jsonify, url_for, flash, session, redirect
from pymongo import MongoClient
from jinja2 import Environment, FileSystemLoader
import os
import bcrypt
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
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
UPLOAD_FOLDER_BARANG = 'static/images/gambar_barang'
UPLOAD_FOLDER_PROFILE ='static/images/profile_pics'
app.config['UPLOAD_FOLDER_BARANG'] = UPLOAD_FOLDER_BARANG
app.config['UPLOAD_FOLDER_PROFILE'] = UPLOAD_FOLDER_PROFILE
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Fungsi untuk memeriksa apakah ekstensi file diperbolehkan

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Context Processor : untuk menyediakan variabel seperti full_name dan profile_pic ke semua template.
@app.context_processor
def inject_user():
    if 'user_id' in session:
        # Ambil data user dari session
        full_name = session.get("full_name", "Guest")
        profile_pic = session.get("profile_pic", None)

        # Pastikan gambar default digunakan jika `profile_pic` kosong
        if not profile_pic:
            profile_pic = "images/profile_pics/default_profile.png"  # Gambar default

        return {
            "full_name": full_name,
            "profile_pic": url_for('static', filename=f"images/profile_pics/{profile_pic}") if profile_pic != "images/profile_pics/default_profile.png" else url_for('static', filename=profile_pic)
        }
    return {
        "full_name": None,
        "profile_pic": None
    }

# Home dan halaman about
@app.route("/")
def home():
    # if 'user_id' in session:
    full_name = session.get("full_name", "Guest")
    return render_template("main/index.html", full_name=full_name)
    # else:
    #     return redirect(url_for('user_login'))

# Rute untuk accounts/admin
@app.route("/admin/dashboard")
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    # Dashboard data
    total_users = db.user.count_documents({})
    total_barang = db.barang.count_documents({})
    total_admin = db.admin.count_documents({})
    total_transaksi = db.transaksi.count_documents(
        {}) if 'transaksi' in db.list_collection_names() else 0
    recent_activities = list(db.activity_log.find().sort('date', -1).limit(10))

    # Data Barang
    barang_data = list(db.barang.find())

    # Data User
    data_user = list(db.user.find({}, {'password': 0}))
    
    # Data Admin
    data_admin = list(db.admin.find({},{'passowrd': 0}))

    return render_template('accounts/admin/dashboard.html',
                           active_page='dashboard',
                           total_users=total_users,
                           total_barang=total_barang,
                           total_admin=total_admin,
                           total_transaksi=total_transaksi,
                           recent_activities=recent_activities,
                           barang_data=barang_data,
                           data_user=data_user,data_admin=data_admin)

# Rute untuk delete admin
@app.route("/accounts/admin/data_admin/delete_admin", methods=["POST"])
def delete_admin():
    admin_id = request.form.get('id')
    admin_collection = db.admin

    # Cari admin berdasarkan ID
    admin = admin_collection.find_one({'_id': ObjectId(admin_id)})

    if admin:
        # Hapus data admin dari database
        result = admin_collection.delete_one({'_id': ObjectId(admin_id)})

        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Admin berhasil dihapus"}), 200
        else:
            return jsonify({"status": "error", "message": "Admin tidak ditemukan"}), 404
    else:
        return jsonify({"status": "error", "message": "Admin tidak ditemukan"}), 404

@app.route("/accounts/admin/logout")
def admin_logout():
    session.clear()
    flash('Anda telah logout', 'success')
    return redirect(url_for('admin_login'))

@app.route("/accounts/admin/login_adm", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('username dan password harus diisi', 'error')
            return redirect(url_for('admin_login'))

        admin = db.admin.find_one({'username': username.lower()})

        if admin and bcrypt.check_password_hash(admin['password'], password):
            session['admin_id'] = str(admin['_id'])
            session['admin_name'] = admin['username']
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('username atau password salah', 'error')
        return redirect(url_for('admin_login'))

    return render_template("accounts/admin/login_adm.html")

@app.route("/accounts/admin/register_adm", methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('Semua field harus diisi', 'error')
            return redirect(url_for('admin_register'))

        existing_admin = db.admin.find_one({'username': username})

        if existing_admin:
            flash('Username atau Email sudah terdaftar', 'error')
            return redirect(url_for('admin_register'))

        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        db.admin.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })

        flash('Registrasi Admin berhasil! Silakan login', 'success')
        return redirect(url_for('admin_login'))

    return render_template("accounts/admin/register_adm.html")

# Rute untuk halaman data barang admin
@app.route("/accounts/admin/data_barang")
def admin_data_barang():
    barang_collection = db.barang
    barang_data = list(barang_collection.find())
    return render_template("accounts/admin/data_barang.html", barang_data=barang_data)

# Rute untuk menambah barang
@app.route("/accounts/admin/data_barang/tambah_barang", methods=["GET", "POST"])
def tambah_barang():
    if request.method == "GET":
        return render_template("accounts/admin/data_barang.html")

    # Proses metode POST
    kategori = request.form.get('kategori')
    brand = request.form.get('brand')
    netto = request.form.get('netto')
    warna = request.form.get('warna')
    harga = request.form.get('harga')
    stock = request.form.get('stock')

    # Mengambil file foto
    foto = request.files.get('foto')
    if foto and allowed_file(foto.filename):
        foto_filename = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER_BARANG'], foto_filename))
    else:
        return jsonify({"status": "error", "message": "File tidak valid atau tidak ada."}), 400

    # Simpan ke database
    db.barang.insert_one({
        "kategori": kategori,
        "brand": brand,
        "netto": netto,
        "warna": warna,
        "harga": harga,
        "stock": stock,
        "foto": foto_filename
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
                app.config['UPLOAD_FOLDER_BARANG'], foto_filename)
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
        foto.save(os.path.join(app.config['UPLOAD_FOLDER_BARANG'], foto_filename))

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

    result = barang_collection.update_one(
        {'_id': ObjectId(barang_id)}, {"$set": update_data})

    if result.modified_count > 0:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Barang tidak ditemukan atau tidak ada perubahan."}), 400

@app.route("/accounts/admin/data_user")
def admin_data_user():
    user_collection = db.user
    user_data = list(user_collection.find())
    return render_template("accounts/admin/data_user.html", user_data=user_data)

# Rute untuk delete user
@app.route("/accounts/admin/data_user/delete_user", methods=["POST"])
def delete_user():
    user_id = request.form.get('id')
    user_collection = db.user

    # Cari user berdasarkan ID
    user = user_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        # Hapus data user dari database
        result = user_collection.delete_one({'_id': ObjectId(user_id)})

        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "User berhasil dihapus"}), 200
        else:
            return jsonify({"status": "error", "message": "User tidak ditemukan"}), 404
    else:
        return jsonify({"status": "error", "message": "User tidak ditemukan"}), 404

# rute untuk register
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

# rute untuk login
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
            session['email'] = user['email']
            session["profile_pic"] = user.get("profile_pic", None) 

            flash('Login berhasil!', 'success')
            # Redirect ke halaman dashboard
            return redirect(url_for('home'))
        else:
            flash('Email atau password salah', 'error')
            return redirect(url_for('user_login'))

    return render_template("accounts/users/login.html")

# route untuk mencek apakah user sudah login atau blum
@app.route("/accounts/users/status", methods=["GET"])
def user_status():
    # Cek apakah ada sesi aktif
    if "user_id" in session:
        return jsonify({
            "is_logged_in": True,
            "full_name": session.get("full_name", "User"),
            "email": session.get("email", "user_email@gmail.com"),
            "profile_pic": session.get("profile_pic",None)
        })
    else:
        return jsonify({
            "is_logged_in": False
        })

# rute unutk edit dan tampilan info user
@app.route("/accounts/users/profile", methods=['GET', 'POST'])
def user_profile():
    if 'user_id' in session and 'email' in session:
        users_collection = db.user
        
        if request.method == "POST":
            # Mendapatkan data form
            full_name = request.form.get("name")
            email = request.form.get("email")
            phone_number = request.form.get("hp")
            profile_pic = request.files.get("profile_pic")
    
            # Validasi data
            if not full_name or not email or not phone_number:
                flash("Semua field harus diisi.", "error")
                return redirect(url_for("user_profile"))

            # Validasi ekstensi file gambar
            if profile_pic and profile_pic.filename != "":
                ext = profile_pic.filename.split(".")[-1].lower()
                if ext not in app.config['ALLOWED_EXTENSIONS']:
                    flash("Hanya file gambar dengan format png, jpg, jpeg, gif yang diizinkan.", "error")
                    return redirect(url_for("user_profile"))

                # Pastikan folder upload ada
                os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)

                # Amankan nama file dan simpan
                filename = secure_filename(profile_pic.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename)
                profile_pic.save(file_path)

                # Simpan path gambar untuk disimpan ke database
                profile_pic_path = filename
            else:
                profile_pic_path = None  # Jika tidak ada gambar baru

            # Update database
            try:
                user_id = ObjectId(session['user_id'])  # Pastikan format ObjectId benar
                update_data = {
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone_number,
                }
                if profile_pic_path:  # Hanya tambahkan jika ada gambar baru
                    update_data["profile_pic"] = profile_pic_path

                users_collection.update_one({"_id": user_id}, {"$set": update_data})

                # Update data session
                session['full_name'] = full_name
                session['email'] = email
                session['phone_number'] = phone_number
                if profile_pic_path:
                    session['profile_pic'] = profile_pic_path

                flash("Profil berhasil diperbarui.", "success")
            except Exception as e:
                flash("Terjadi kesalahan saat memperbarui profil.", "error")
                print(f"Error: {e}")

            return redirect(url_for("user_profile"))

        # Jika GET, ambil data user dari database
        try:
            user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
            if not user:
                flash("User tidak ditemukan.", "error")
                return redirect(url_for("user_login"))
        except Exception as e:
            flash("Terjadi kesalahan saat mengambil data user.", "error")
            print(f"Error: {e}")
            return redirect(url_for("user_login"))

        # Data untuk ditampilkan di halaman profil
        full_name = user.get("full_name", "Guest")
        email = user.get("email", "user_email@gmail.com")
        phone_number = user.get("phone_number", "No.Handphone ")
        profile_pic = user.get("profile_pic", None)

        return render_template(
            "accounts/users/profile.html",
            full_name=full_name,
            email=email,
            phone_number=phone_number,
        )
    else:
        flash("Anda harus login terlebih dahulu.", "error")
        return redirect(url_for('user_login'))
    
# route logout
@app.route("/accounts/users/logout", methods=["GET"])
def user_logout():
    # Hapus sesi user
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("home"))

# rute untuk reset password
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

# rute untuk lupa password
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

@app.route("/accounts/users/edit_password", methods=["GET", "POST"])
def edit_password():
    if "user_id" in session and "email" in session:
        email = session["email"]

        if request.method == "POST":
            # Ambil data dari form
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            # Validasi input
            if not current_password or not new_password or not confirm_password:
                return jsonify({"status": "error", "message": "Semua field harus diisi!"}), 400

            if new_password != confirm_password:
                return jsonify({"status": "error", "message": "Password baru dan konfirmasi password tidak cocok!"}), 400

            # Ambil data user dari database
            users_collection = db.user
            user = users_collection.find_one({"email": email})

            if not user:
                return jsonify({"status": "error", "message": "User tidak ditemukan!"}), 404

            # Validasi password lama
            if not bcrypt.check_password_hash(user['password'], current_password):
                return jsonify({"status": "error", "message": "Password lama Anda salah!"}), 400

            # Hash password baru
            hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

            # Update password di database
            try:
                users_collection.update_one(
                    {"_id": ObjectId(user["_id"])},
                    {"$set": {"password": hashed_new_password}}
                )
                flash("Password berhasil diperbarui.", "success")
                return jsonify({"status": "success", "message": "Password berhasil diperbarui!"}), 200
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({"status": "error", "message": "Terjadi kesalahan saat memperbarui password."}), 500

        # Jika GET, tampilkan halaman edit password
        return render_template("accounts/users/edit_password.html", email=email)
    else:
        return redirect(url_for("user_login"))

# Rute untuk products


@app.route("/products/product_lists")
def product_lists():
    if 'user_id' in session:
        barang_collection = db.barang
        barang_data = list(barang_collection.find())
        return render_template("products/product_lists.html", barang_data=barang_data)
    else:
        return redirect(url_for('user_login'))
    
# filter data
@app.route("/products/product_lists/filter", methods=["GET"])
def filter_products():
    # if 'user_id' in session:
    kategori = request.args.get('kategori',' ').upper()
    print(request.args.get('kategori'))
    barang_collection = db.barang

    if kategori and kategori != "ALL":
       # Cari dengan case-insensitive menggunakan regex
        barang_data = list(barang_collection.find({"kategori": {"$regex": f"^{kategori}$", "$options": "i"}}))
    else:
        barang_data = list(barang_collection.find())

    return render_template("products/product_list_filter.html", barang_data=barang_data)
    # else:
    #     return redirect(url_for('user_login'))

# route produk detail
@app.route("/products/product_details/<product_id>")
def product_details(product_id):
    if "user_id" in session:
        barang_collection = db.barang

        # Ambil produk berdasarkan ID
        product = barang_collection.find_one({"_id": ObjectId(product_id)})

        if not product:
            flash("Produk tidak ditemukan!", "error")
            return redirect(url_for("product_lists"))  # Kembali ke daftar produk

        # Konversi harga ke tipe integer atau float
        product['harga'] = float(product['harga'])  # Ubah ke float atau int sesuai kebutuhan

        return render_template("products/product_details.html", product=product)
    else:
        return redirect(url_for("user_login"))



# route tambek ke keranjang
@app.route("/products/product_details/add", methods=["POST"])
def add_to_cart():
    if "user_id" in session:
        try:
            product_id = ObjectId(request.form.get("product_id"))
        except:
            return jsonify({"message": "ID produk tidak valid"}), 400

        quantity = request.form.get("quantity")
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": "Jumlah tidak valid"}), 400

        barang_collection = db.barang
        cart_collection = db.cart

        # Ambil produk berdasarkan ID
        product = barang_collection.find_one({"_id": product_id})

        if not product:
            return jsonify({"message": "Produk tidak ditemukan"}), 404

        if product["stok"] < quantity:
            return jsonify({"message": "Stok tidak mencukupi"}), 400

        # Tambahkan ke keranjang
        cart_collection.insert_one({
            "user_id": session["user_id"],
            "product_id": str(product_id),
            "quantity": quantity,
            "added_at": datetime.now(),
        })

        # Kurangi stok di koleksi barang
        barang_collection.update_one(
            {"_id": product_id},
            {"$inc": {"stok": -quantity}}
        )

        return jsonify({"message": "Produk berhasil ditambahkan ke keranjang"}), 200
    else:
        return jsonify({"message": "Harap login terlebih dahulu"}), 401

# Rute untuk carts
@app.route("/carts/order_history")
def order_history():
    if 'user_id' in session:
        full_name = session.get("full_name", "Guest")
        return render_template("carts/order_history.html", full_name=full_name)
    else:
        return redirect(url_for('user_login'))

@app.route("/carts/order_summary")
def order_summary():
    if 'user_id' in session:
        full_name = session.get("full_name", "Guest")
        return render_template("carts/order_summary.html", full_name=full_name)
    else:
        return redirect(url_for('user_login'))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)