import os
from datetime import datetime, timedelta
from supabase import create_client, Client

# Mengambil fungsi dari script yang sudah Anda buat
from scrape_metar_bmkg import scrape_wals
from parse_metar_structured import parse_one_line

def run_pipeline():
    # 1. Hubungkan ke Supabase (Kredensial disembunyikan via Environment Variables)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    # 2. Tentukan waktu penarikan (misal: 24 jam terakhir agar aman jika ada yang terlewat)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=1)

    print(f"Mulai scraping dari {start_dt} hingga {end_dt}...")
    
    # 3. Tarik data mentah menggunakan fungsi Anda
    raw_lines = scrape_wals(start_dt, end_dt)
    
    # 4. Parse data menjadi format dictionary terstruktur
    parsed_data = []
    for line in raw_lines:
        parsed = parse_one_line(line)
        # Pastikan data memiliki waktu valid yang terisi
        if parsed and parsed.get('valid_time_utc'): 
            # Buang kunci yang tidak ada di tabel Supabase agar tidak error
            parsed.pop('weather_phenomena', None)
            parsed.pop('sky_layer1_cover', None)
            parsed.pop('sky_layer1_height_ft', None)
            parsed.pop('sky_layer2_cover', None)
            parsed.pop('sky_layer2_height_ft', None)
            parsed.pop('sky_layer3_cover', None)
            parsed.pop('sky_layer3_height_ft', None)
            
            parsed_data.append(parsed)

    # 5. Upload ke database menggunakan metode Upsert (Insert/Update)
    if parsed_data:
        response = supabase.table("metar_wals").upsert(parsed_data).execute()
        print(f"Sukses! {len(parsed_data)} baris data METAR berhasil diunggah ke Supabase.")
    else:
        print("Tidak ada data baru untuk diunggah.")

if __name__ == "__main__":
    run_pipeline()