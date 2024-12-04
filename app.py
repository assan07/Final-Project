from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

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
    return render_template('main/index.html')

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
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
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
    
@app.route("/accounts/admin/data_user")
def admin_data_user():
    return render_template("accounts/admin/data_user.html")

@app.route("/accounts/admin/login_adm")
def admin_login():
    return render_template("accounts/admin/login_adm.html")

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

# Rute untuk products
@app.route("/products/product_details")
def product_details():
    return render_template("products/product_details.html")

@app.route("/products/product_lists")
def product_lists():
    return render_template("products/product_lists.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
