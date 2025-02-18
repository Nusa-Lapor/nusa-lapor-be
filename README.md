# NusaLapor

**Solusi Pelaporan Gapake Ribet!**

## Instalasi dan Cara Menjalankan 📌

Dalam development NusaLapor, kami memakai _techstack_ Django sebagai _backend_, Next.js sebagai _frontend_, dan Supabase / PostgreSQL sebagai basis data yang digunakan.

### 1. Instalasi Project🙌

Untuk memulai dari project *backend* ini, berikut langkah-langkah yang bisa dikerjakan:

1. Melakukan cloning project ke local
```git
git clone https://github.com/Nusa-Lapor/nusa-lapor-be.git
```

2. Instalasi requirements dari requirements.txt yang sudah ada
```terminal
pip install -r requirments.txt
```

3. Masuk ke `development` environments

**`Windows`**
```terminal
python -m venv env
env\Scripts\activate
python manage.py runserver
```

**`macOS`**
```terminal
python3 -m venv env 
source env/bin/activate
python3 manage.py runserver
```

Dengan menyelesaikan langkah-langkah berikut, project *backend* Django ini siap dikembangkan (develop). Untuk melihat progres *development* silakan membuka `http://127.0.0.1:8000/` atau `http://localhost:8000/`

### 2. Instalasi Packages📦

Untuk melengkapi project *backend* ini, ada beberapa packages yang harus diinstal:

1. Instalasi PostgreSQL
- Silakan instalasi **PostgreSQL** dari [🔗website resminya](https://www.postgresql.org/download/) dan ikuti instruksinya.
> **Catatan:** Pastikan untuk menginstal PostgreSQL versi 17. Jangan lupa untuk mencatat password superuser (nama: postgres) untuk PostgreSQL.
- Tambahkan `C:Program Files\PostgreSQL\17\bin` ke PATH System Environment Variables. Silakan merefer kepada internet, salah satunya adalah: [🔗tutorial menambahkan ke PATH](https://www.java.com/en/download/help/path.html)

2. Menerapkan PostgreSQL untuk fase `development` di `localhost`
- Buat file `.env` di root project directory (1 dir dengan `README.md`) terlebih dahulu dengan detail seperti berikut:
```env
# Local PostgreSQL database configuration
LOCAL_DATABASE_ENGINE=django.db.backends.postgresql
LOCAL_DATABASE_HOST=localhost
LOCAL_DATABASE_NAME=nusalapordb
LOCAL_DATABASE_USER=nama_user_anda
LOCAL_DATABASE_PORT=5432 # default -> 5432
LOCAL_DATABASE_PASSWORD=password_user_anda

# Supabase PostgreSQL database configuration
PROD_DATABASE_ENGINE=django.db.backends.postgresql
PROD_DATABASE_HOST=aws-0-ap-southeast-1.pooler.supabase.com
PROD_DATABASE_NAME=postgres
PROD_DATABASE_USER=nama_user_supabase
PROD_DATABASE_PORT=6543 # 6543 -> transaction, 5432 -> session / default
PROD_DATABASE_PASSWORD=password_supabase
```
> **Catatan:** untuk PROD DB details bisa ditanyakan kepada owner
- Tambahkan role bernama **"user"** Anda di PC tempat bekerja ke PostgreSQL. Nama **"user"** bisa dilihat seperti pada `C:Users\user` (nama **user** menyesuaikan dengan PC Anda).
> Masuk ke postgres sebagai `superuser`
```terminal
psql -U postgres
```
> Selanjutnya masukkan password yang sudah dibuat dari instalasi PostgreSQL dan tampilan terminal akan berubah menjadi
```terminal
postgres=> 
```
> Jika sudah demikian, maka kalian harus membuat role menyesuaikan nama **user** Anda. Maka, Anda diperkenankan menulis **(jangan menulis `\q` terlebih dahulu jika tidak ingin keluar dari menu superuser PostgreSQL postgres)
```terminal
CREATE ROLE user WITH LOGIN PASSWORD password;
ALTER ROLE user CREATEDB;
\q
```
> Ubah `user` menjadi nama **user** Anda dan `password` dengan password yang Anda buat. Jangan lupa untuk menyimpan passwordnya. Selanjutnya, buatlah database bernama `nusalapordb` untuk database local
```terminal
createdb nusalapor
```
> Kalian akan memasukkan password untuk role **user** yang tadi sudah dibuat. Untuk memastikan bahwa pembuatan database berhasil, masuk ke menu databasenya dengan (ganti `user` dengan nama user Anda sendiri)
```terminal
psql -U user -d nusalapor
```
> Selanjutnya tampilan terminal akan menjadi
```terminal
nusalapordb =>
```
> Jika demikian, maka Anda telah berhasil menambahkan database local Anda. **Jangan lupa untuk mengubah variabel `.env` untuk `LOCAL_DATABASE_USER` dan `LOCAL_DATABASE_PASSWORD` menjadi nama role/user dan passwordnya yang sudah dibuat.

### 3. Catatan tambahan📝

Anda bisa _spend_ waktu untuk mempelajari dokumentasi _techstack_ yang digunakan dengan _hyperlink_ di bawah ini:

- [PostgreSQL](https://postgresql.org)
- [Supabase](https://supabase.com)
- [Next.js](https://nextjs.org)
- [Django](https://www.djangoproject.com/)
- **TBD (unconfirmed):** [Drizzle ORM](https://orm.drizzle.team)

### 4. Deployment
**TBA**