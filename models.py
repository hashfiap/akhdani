from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Kota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    provinsi = db.Column(db.String(100), nullable=False)
    pulau = db.Column(db.String(100), nullable=False)
    is_luar_negeri = db.Column(db.Boolean, default=False)

class Perdin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    maksud_tujuan = db.Column(db.Text, nullable=False)
    tgl_berangkat = db.Column(db.Date, nullable=False)
    tgl_pulang = db.Column(db.Date, nullable=False)
    
    kota_asal_id = db.Column(db.Integer, db.ForeignKey('kota.id'), nullable=False)
    kota_tujuan_id = db.Column(db.Integer, db.ForeignKey('kota.id'), nullable=False)
    
    durasi_hari = db.Column(db.Integer)
    jarak_km = db.Column(db.Float)
    total_uang_saku = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='Pending')

    kota_asal = db.relationship('Kota', foreign_keys=[kota_asal_id])
    kota_tujuan = db.relationship('Kota', foreign_keys=[kota_tujuan_id])
    user = db.relationship('User', backref='perdin_list')