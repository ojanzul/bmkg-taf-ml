import os
from datetime import datetime, timedelta

from supabase import create_client

from scrape_metar_bmkg import (
    scrape_wals
)

from parse_metar_structured import (
    parse_one_line
)


# ============================================================
# RUN PIPELINE
# ============================================================

def run_pipeline():

    print("")
    print("=" * 60)
    print("BMKG METAR DATA PIPELINE")
    print("=" * 60)

    # ========================================================
    # STEP 1
    # TENTUKAN RENTANG WAKTU
    # ========================================================

    end_dt = datetime.utcnow()

    start_dt = (
        end_dt
        - timedelta(days=1)
    )

    print("")

    print(
        "Start time:",
        start_dt
    )

    print(
        "End time:",
        end_dt
    )

    # ========================================================
    # STEP 2
    # SCRAPE DATA BMKG
    # ========================================================

    print("")
    print(
        "STEP 1: Scraping BMKG..."
    )

    raw_lines = scrape_wals(

        start_dt,

        end_dt

    )

    # ========================================================
    # VALIDASI HASIL SCRAPING
    # ========================================================

    if not raw_lines:

        print("")
        print(
            "ERROR: Tidak ada data METAR yang berhasil diambil."
        )

        print(
            "Pipeline dihentikan."
        )

        raise RuntimeError(
            "BMKG scraping returned no data."
        )

    print("")

    print(
        "Data mentah berhasil diambil:",
        len(raw_lines)
    )

    # ========================================================
    # STEP 3
    # PARSING METAR
    # ========================================================

    print("")
    print(
        "STEP 2: Parsing METAR..."
    )

    parsed_data = []

    failed_count = 0

    for index, line in enumerate(
        raw_lines,
        start=1
    ):

        print(
            f"Parsing {index}/{len(raw_lines)}"
        )

        try:

            parsed = parse_one_line(
                line
            )

            if parsed:

                if parsed.get(
                    "valid_time_utc"
                ):

                    parsed_data.append(
                        parsed
                    )

                else:

                    print(
                        "WARNING: "
                        "valid_time_utc kosong."
                    )

            else:

                failed_count += 1

                print(
                    "WARNING: "
                    "Parsing menghasilkan None."
                )

        except Exception as e:

            failed_count += 1

            print(
                "ERROR parsing:"
            )

            print(
                line
            )

            print(
                e
            )

    # ========================================================
    # HASIL PARSING
    # ========================================================

    print("")
    print(
        "Parsing selesai."
    )

    print(
        "Berhasil:",
        len(parsed_data)
    )

    print(
        "Gagal:",
        failed_count
    )

    # ========================================================
    # JIKA TIDAK ADA DATA VALID
    # ========================================================

    if not parsed_data:

        print("")
        print(
            "ERROR: Tidak ada data valid."
        )

        raise RuntimeError(
            "No valid METAR data after parsing."
        )

    # ========================================================
    # STEP 4
    # CONNECT SUPABASE
    # ========================================================

    print("")
    print(
        "STEP 3: Connecting to Supabase..."
    )

    supabase_url = os.environ.get(
        "SUPABASE_URL"
    )

    supabase_key = os.environ.get(
        "SUPABASE_KEY"
    )

    if not supabase_url:

        raise RuntimeError(
            "SUPABASE_URL belum diset."
        )

    if not supabase_key:

        raise RuntimeError(
            "SUPABASE_KEY belum diset."
        )

    supabase = create_client(

        supabase_url,

        supabase_key

    )

    print(
        "Supabase connection berhasil."
    )

    # ========================================================
    # STEP 5
    # UPLOAD DATA
    # ========================================================

    print("")
    print(
        "STEP 4: Upload data ke Supabase..."
    )

    try:

        response = (

            supabase

            .table(
                "metar_wals"
            )

            .upsert(
                parsed_data
            )

            .execute()

        )

        print("")
        print(
            "Upload berhasil."
        )

        print(
            "Jumlah data:",
            len(parsed_data)
        )

        print(
            "Response:",
            response
        )

    except Exception as e:

        print("")
        print(
            "ERROR saat upload ke Supabase:"
        )

        print(
            e
        )

        raise

    # ========================================================
    # SELESAI
    # ========================================================

    print("")
    print("=" * 60)
    print(
        "PIPELINE SELESAI"
    )
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_pipeline()
