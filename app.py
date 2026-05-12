from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Kota, Perdin
from logic import calculate_distance, calculate_duration, get_daily_allowance
from datetime import datetime
import os

app = Flask(__name__, template_folder="ui")
app.secret_key = 'akhdani_secret_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'perdin.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- Initialize Data ---
def seed_data():
    if not Kota.query.first():
        bandung = Kota(nama="Kota Bandung", latitude=-6.917500, longitude=107.619100, 
                       provinsi="Jawa Barat", pulau="Jawa", is_luar_negeri=False)
        surabaya = Kota(nama="Surabaya", latitude=-7.257500, longitude=112.752100, 
                        provinsi="Jawa Timur", pulau="Jawa", is_luar_negeri=False)
        malang = Kota(nama="Malang", latitude=-7.979700, longitude=112.630400, 
                        provinsi="Jawa Timur", pulau="Jawa", is_luar_negeri=False)
        sumbawa = Kota(nama="Sumbawa", latitude=-8.493100, longitude=117.420200, 
                        provinsi="Nusa Tenggara Barat", pulau="Sumbawa", is_luar_negeri=False)
        melbourne = Kota(nama="Melbourne", latitude=-37.813600, longitude=144.963100, 
                        provinsi="-", pulau="Australia", is_luar_negeri=True)
        db.session.add_all([bandung, surabaya, malang, sumbawa, melbourne])
        db.session.commit()
        
    if not User.query.filter_by(username="admin").first():
        user1 = User(username="pegawai1", password="123", role="PEGAWAI")
        sdm1 = User(username="sdm1", password="123", role="DIVISI-SDM")
        admin1 = User(username="admin", password="123", role="ADMIN")
        db.session.add_all([user1, sdm1, admin1])
        db.session.commit()

# --- Routes ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        
        else:
            flash("Username or Password is wrong")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if session['role'] == 'PEGAWAI':
        perdin_list = Perdin.query.filter_by(employee_id=session['user_id']).all()
    else:
        perdin_list = Perdin.query.all()
        
    return render_template('dashboard.html', perdin=perdin_list)

@app.route('/tambah_perdin', methods=['GET', 'POST'])
def tambah_perdin():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    kotas = Kota.query.all()
    
    if request.method == 'POST':
        maksud = request.form['maksud']
        tgl_b = datetime.strptime(request.form['tgl_berangkat'], '%Y-%m-%d')
        tgl_p = datetime.strptime(request.form['tgl_pulang'], '%Y-%m-%d')
        asal_id = request.form['kota_asal']
        tujuan_id = request.form['kota_tujuan']
        
        kota_asal = Kota.query.get(asal_id)
        kota_tujuan = Kota.query.get(tujuan_id)
        
        dist = calculate_distance(kota_asal.latitude, kota_asal.longitude, 
                                  kota_tujuan.latitude, kota_tujuan.longitude)
        days = calculate_duration(tgl_b, tgl_p)
        rate, currency = get_daily_allowance(kota_asal, kota_tujuan, dist)
        
        new_perdin = Perdin(
            employee_id=session['user_id'],
            maksud_tujuan=maksud,
            tgl_berangkat=tgl_b,
            tgl_pulang=tgl_p,
            kota_asal_id=asal_id,
            kota_tujuan_id=tujuan_id,
            durasi_hari=days,
            jarak_km=round(dist, 2),
            total_uang_saku=rate * days if currency == "IDR" else rate * days
        )
        db.session.add(new_perdin)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('form_perdin.html', kotas=kotas)

@app.route('/check/<int:id>')
def check_perdin(id):
    if session.get('role') != 'DIVISI-SDM': 
        return redirect(url_for('dashboard'))
    
    perdin = Perdin.query.get_or_404(id)
    return render_template('verif.html', p=perdin)

@app.route('/approve/<int:id>/<string:action>')
def approve_perdin(id, action):
    if session.get('role') != 'DIVISI-SDM': return redirect(url_for('dashboard'))
    
    perdin = Perdin.query.get(id)
    if perdin:
        perdin.status = 'Approved' if action == 'Approve' else 'Rejected'
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/users')
def manage_users():
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    all_users = User.query.all()
    return render_template('manage_users.html', users=all_users)

@app.route('/change_role/<int:id>', methods=['POST'])
def change_role(id):
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    
    user = User.query.get(id)
    if user and user.username != 'admin':
        new_role = request.form.get('role')
        user.role = new_role
        db.session.commit()
        flash(f"Role for {user.username} updated to {new_role}")
    
    return redirect(url_for('manage_users'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_perdin(id):
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
        
    perdin = Perdin.query.get_or_404(id)
    kotas = Kota.query.all()
    
    if request.method == 'POST':
        perdin.maksud_tujuan = request.form['maksud']
        perdin.tgl_berangkat = datetime.strptime(request.form['tgl_berangkat'], '%Y-%m-%d')
        perdin.tgl_pulang = datetime.strptime(request.form['tgl_pulang'], '%Y-%m-%d')
        perdin.kota_asal_id = request.form['kota_asal']
        perdin.kota_tujuan_id = request.form['kota_tujuan']
        
        kota_asal = Kota.query.get(perdin.kota_asal_id)
        kota_tujuan = Kota.query.get(perdin.kota_tujuan_id)
        
        dist = calculate_distance(kota_asal.latitude, kota_asal.longitude, 
                                  kota_tujuan.latitude, kota_tujuan.longitude)
        days = calculate_duration(perdin.tgl_berangkat, perdin.tgl_pulang)
        rate, _ = get_daily_allowance(kota_asal, kota_tujuan, dist)
        
        perdin.durasi_hari = days
        perdin.jarak_km = round(dist, 2)
        perdin.total_uang_saku = rate * days
        
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_perdin.html', p=perdin, kotas=kotas)

@app.route('/delete/<int:id>')
def delete_perdin(id):
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    
    perdin = Perdin.query.get(id)
    if perdin:
        db.session.delete(perdin)
        db.session.commit()
        flash("Data deleted successfully")
    return redirect(url_for('dashboard'))

@app.route('/kotas')
def master_kota():
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    kotas = Kota.query.all()
    return render_template('master_kota.html', kotas=kotas)

@app.route('/add_kota', methods=['GET', 'POST'])
def add_kota():
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        new_kota = Kota(
            nama=request.form['nama'],
            latitude=float(request.form['lat']),
            longitude=float(request.form['lon']),
            provinsi=request.form['provinsi'],
            pulau=request.form['pulau'],
            is_luar_negeri='is_luar_negeri' in request.form
        )
        db.session.add(new_kota)
        db.session.commit()
        flash("City added successfully!")
        return redirect(url_for('master_kota'))
        
    return render_template('form_kota.html', kota=None)

@app.route('/edit_kota/<int:id>', methods=['GET', 'POST'])
def edit_kota(id):
    if session.get('role') != 'ADMIN': 
        return redirect(url_for('dashboard'))
    
    kota = Kota.query.get_or_404(id)
    if request.method == 'POST':
        kota.nama = request.form['nama']
        kota.latitude = float(request.form['lat'])
        kota.longitude = float(request.form['lon'])
        kota.provinsi = request.form['provinsi']
        kota.pulau = request.form['pulau']
        kota.is_luar_negeri = 'is_luar_negeri' in request.form
        
        db.session.commit()
        flash("City updated successfully!")
        return redirect(url_for('master_kota'))
        
    return render_template('form_kota.html', kota=kota)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)