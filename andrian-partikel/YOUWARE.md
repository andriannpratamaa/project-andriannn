# ANDRIAN - Sistem Partikel Interaktif Berbasis Gestur

Sistem partikel 3D real-time yang dikendalikan oleh gerakan tangan, dibangun dengan React, Three.js, dan MediaPipe.

## Ringkasan Proyek

Andrian memungkinkan pengguna memanipulasi awan partikel 3D menggunakan gerakan tangan yang ditangkap melalui webcam. Sistem ini melacak gestur tangan untuk mengubah formasi partikel secara real-time, menawarkan pengalaman visual yang memukau.

## Fitur Utama

-   **Kontrol Gestur Cerdas**: Menggunakan MediaPipe Hand Tracking untuk mendeteksi gestur spesifik.
    -   **Tangan Mengepal (Fist)**: Membentuk formasi Galaksi Cincin (Saturnus-like).
    -   **Tangan Terbuka (Open)**: Meledakkan/menyebarkan partikel (Explosion effect).
    -   **Tanda V (Victory)**: Membentuk teks "I LOVE U" dari partikel.
    -   **Tanda Metal (Rock)**: Membentuk Hati (Heart) yang berdetak.
-   **Efek Gyro**: Partikel mengikuti posisi tangan pengguna dengan sensitivitas tinggi, memberikan efek paralaks yang responsif.
-   **Sistem Partikel 3D**: Rendering performa tinggi menggunakan Three.js (`@react-three/fiber`) dengan 8000 partikel.
-   **Visual Kustom**:
    -   Tema warna Biru Neon yang futuristik.
    -   Transisi halus (smooth morphing) antar formasi.
-   **UI Minimalis**: Antarmuka bersih tanpa gangguan, fokus pada visualisasi.

## Teknologi

-   **Frontend**: React 18, TypeScript, Vite
-   **3D Graphics**: Three.js, @react-three/fiber, @react-three/drei
-   **Computer Vision**: MediaPipe Tasks Vision (Hand Landmarker)
-   **State Management**: Zustand
-   **Styling**: Tailwind CSS

## Cara Penggunaan

1.  Izinkan akses kamera saat diminta.
2.  Arahkan tangan ke kamera (Preview kamera ada di pojok kiri bawah, diperbesar).
3.  **Kepalkan Tangan**: Lihat formasi Galaksi Cincin.
4.  **Buka Tangan**: Ledakkan partikel.
5.  **Bentuk Huruf V (Peace)**: Tampilkan pesan "I LOVE U".
6.  **Bentuk Tanda Metal (Rock)**: Tampilkan bentuk Hati.
7.  **Gerakkan Tangan**: Partikel akan berotasi mengikuti gerakan tangan Anda.

## Catatan Pengembangan

-   **Performa**: Menggunakan `BufferGeometry` untuk rendering ribuan partikel tanpa lag.
-   **AI Model**: Model Hand Landmarker dimuat dari CDN.
-   **Posisi Tangan**: Koordinat tangan dinormalisasi untuk mengontrol rotasi scene (efek gyro).
