
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
        phone_number = user.get("phone_number", "0812345678")
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