# NatsuPy

Repositori ini berisi source code pada paper dengan judul *NatsuPy: Reduksi
Noise pada Pengukuran Suhu berbasis Sensor Pyroelectric DS18B20 menggunakan
Kalman Filter* oleh Fahmi Noor Fiqri.

Untuk menjalankan aplikasi pada repositori ini, Anda perlu sebuah Arduino atau
mikrokontroler lain yang dapat memberikan data melalui protokol serial. Pada
repositori ini terdapat sampel kode untuk DHT22 pada file `natsupyhw.ino`.
Selain itu, Anda akan membutuhkan virtual environment Python untuk menjalankan
program `app.py` untuk merekam data dari sensor dan menampilkan outputnya secara
real-time.

Secara umum prosedur untuk menjalankan program ini yaitu:

1. Clone repositori ini.
2. Upload `natsupyhw_dht22.ino` atau `natsupyhw_ds18b20.ino` ke board Arduino dengan mengikuti instruksi
   konfigurasi pin seperti yang terdapat pada file tersebut.
3. Buat environment baru menggunakan `conda` atau `pip` menggunakan file
   `requirements.txt` atau `conda.yml`.
4. Jalankan perintah `python app.py` untuk menjalankan program.
5. Inputkan COM port dan baud rate yang digunakan pada board Arduino.
6. Klik **Connect** untuk memulai proses perekaman data.
