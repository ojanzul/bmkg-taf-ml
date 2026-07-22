import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


BASE_URL = "https://web-aviation.bmkg.go.id/web/metar_speci.php"


# ============================================================
# HTTP HEADERS
# ============================================================

HEADERS_COMMON = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://web-aviation.bmkg.go.id/",
    "Connection": "keep-alive",
}


# ============================================================
# CREATE SESSION
# ============================================================

def create_session():

    session = requests.Session()

    session.headers.update(HEADERS_COMMON)

    return session


# ============================================================
# GET CSRF TOKEN
# ============================================================

def get_csrf_token(session):

    print("Mengakses halaman BMKG...")

    try:

        response = session.get(
            BASE_URL,
            timeout=30,
            allow_redirects=True
        )

        print("HTTP Status:", response.status_code)
        print("Final URL:", response.url)

        print(
            "Content-Type:",
            response.headers.get("Content-Type")
        )

        print(
            "Response Length:",
            len(response.text)
        )

        # ====================================================
        # DETEKSI 403
        # ====================================================

        if response.status_code == 403:

            print("")
            print("=" * 60)
            print("ERROR 403 FORBIDDEN")
            print("=" * 60)

            print(
                "Server BMKG menolak request dari environment "
                "GitHub Actions."
            )

            print("")
            print("Kemungkinan penyebab:")
            print("1. IP GitHub Actions diblokir")
            print("2. WAF / Anti Bot BMKG")
            print("3. Endpoint membutuhkan browser asli")
            print("4. Endpoint berubah")
            print("5. Akses otomatis dibatasi")

            print("")
            print("Response awal:")

            print(response.text[:1000])

            print("=" * 60)

            return None

        # ====================================================
        # ERROR LAIN
        # ====================================================

        response.raise_for_status()

        # ====================================================
        # PARSE HTML
        # ====================================================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # ====================================================
        # COBA CARI CSRF META
        # ====================================================

        token_meta = soup.find(
            "meta",
            attrs={
                "name": "csrf-token"
            }
        )

        if token_meta:

            token = token_meta.get("content")

            if token:

                print(
                    "CSRF token ditemukan melalui meta tag."
                )

                return token

        # ====================================================
        # COBA CARI CSRF INPUT
        # ====================================================

        token_input = soup.find(
            "input",
            attrs={
                "name": "_token"
            }
        )

        if token_input:

            token = token_input.get("value")

            if token:

                print(
                    "CSRF token ditemukan melalui input."
                )

                return token

        # ====================================================
        # CSRF TIDAK DITEMUKAN
        # ====================================================

        print(
            "PERINGATAN: CSRF token tidak ditemukan."
        )

        print(
            "Mungkin website BMKG tidak menggunakan "
            "CSRF token seperti yang diasumsikan."
        )

        return None

    except requests.exceptions.Timeout:

        print(
            "ERROR: Request ke BMKG timeout."
        )

        return None

    except requests.exceptions.ConnectionError as e:

        print(
            "ERROR: Gagal terhubung ke server BMKG."
        )

        print(e)

        return None

    except requests.exceptions.RequestException as e:

        print(
            "ERROR HTTP saat mengakses BMKG:"
        )

        print(e)

        return None

    except Exception as e:

        print(
            "ERROR tidak terduga:"
        )

        print(e)

        return None


# ============================================================
# SCRAPE WALS
# ============================================================

def scrape_wals(
    start_dt: datetime,
    end_dt: datetime,
    max_retries=3
):

    session = create_session()

    print("")
    print("=" * 60)
    print("MULAI SCRAPING BMKG")
    print("=" * 60)

    print(
        "Periode:",
        start_dt,
        "hingga",
        end_dt
    )

    # ========================================================
    # STEP 1 - GET CSRF
    # ========================================================

    csrf_token = None

    for attempt in range(
        1,
        max_retries + 1
    ):

        print(
            f"Percobaan mendapatkan CSRF "
            f"{attempt}/{max_retries}"
        )

        csrf_token = get_csrf_token(
            session
        )

        if csrf_token:

            break

        if attempt < max_retries:

            print(
                "Menunggu 5 detik sebelum retry..."
            )

            time.sleep(5)

    # ========================================================
    # JIKA GAGAL MENDAPATKAN CSRF
    # ========================================================

    if not csrf_token:

        print("")
        print(
            "CSRF token tidak tersedia."
        )

        print(
            "Scraping dihentikan."
        )

        return []

    # ========================================================
    # STEP 2 - POST REQUEST
    # ========================================================

    payload = {

        "_token": csrf_token,

        "station": "WALS",

        "start": start_dt.strftime(
            "%Y-%m-%dT%H:%M"
        ),

        "end": end_dt.strftime(
            "%Y-%m-%dT%H:%M"
        ),

    }

    headers = {

        **HEADERS_COMMON,

        "Content-Type":
            "application/x-www-form-urlencoded",

        "Origin":
            "https://web-aviation.bmkg.go.id",

    }

    print("")
    print(
        "Mengirim request data METAR WALS..."
    )

    try:

        response = session.post(

            BASE_URL,

            data=payload,

            headers=headers,

            timeout=30,

            allow_redirects=True

        )

        print(
            "POST HTTP Status:",
            response.status_code
        )

        print(
            "POST Final URL:",
            response.url
        )

        response.raise_for_status()

    except requests.exceptions.HTTPError as e:

        print(
            "ERROR HTTP saat mengambil data METAR:"
        )

        print(e)

        print(
            "Response:",
            response.text[:1000]
        )

        return []

    except Exception as e:

        print(
            "ERROR saat POST ke BMKG:"
        )

        print(e)

        return []

    # ========================================================
    # STEP 3 - PARSE RESPONSE
    # ========================================================

    return parse_metar_lines(
        response.text
    )


# ============================================================
# PARSE METAR LINES
# ============================================================

def parse_metar_lines(
    html_text
):

    soup = BeautifulSoup(
        html_text,
        "html.parser"
    )

    # ========================================================
    # AMBIL TEXT BERSIH
    # ========================================================

    text = soup.get_text(
        "\n",
        strip=True
    )

    # ========================================================
    # REGEX METAR / SPECI
    # ========================================================

    pattern = re.compile(

        r"\b("
        r"(?:METAR|SPECI)"
        r"\s+"
        r"[A-Z]{4}"
        r"\s+"
        r"\d{6}Z"
        r".*?"
        r"="
        r")",

        re.DOTALL

    )

    matches = pattern.findall(
        text
    )

    results = []

    for match in matches:

        # ====================================================
        # NORMALISASI SPASI
        # ====================================================

        clean_line = " ".join(
            match.split()
        )

        results.append(
            clean_line
        )

    # ========================================================
    # REMOVE DUPLICATE
    # ========================================================

    results = list(
        dict.fromkeys(
            results
        )
    )

    print("")
    print(
        "Jumlah METAR/SPECI ditemukan:",
        len(results)
    )

    for item in results:

        print(
            item
        )

    return results


# ============================================================
# TEST MANUAL
# ============================================================

if __name__ == "__main__":

    from datetime import timedelta

    end_dt = datetime.utcnow()

    start_dt = (
        end_dt
        - timedelta(days=1)
    )

    data = scrape_wals(
        start_dt,
        end_dt
    )

    print("")
    print(
        "Total data:",
        len(data)
    )
