import requests


URL = (
    "https://web-aviation.bmkg.go.id/"
    "web/metar_speci.php"
)


HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 "
        "Safari/537.36"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),

    "Accept-Language":
        "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",

    "Referer":
        "https://web-aviation.bmkg.go.id/",

}


print("=" * 60)

print(
    "TEST AKSES BMKG"
)

print("=" * 60)


try:

    response = requests.get(

        URL,

        headers=HEADERS,

        timeout=30,

        allow_redirects=True

    )

    print("")

    print(
        "HTTP Status:",
        response.status_code
    )

    print(
        "Final URL:",
        response.url
    )

    print(
        "Server:",
        response.headers.get(
            "Server"
        )
    )

    print(
        "Content-Type:",
        response.headers.get(
            "Content-Type"
        )
    )

    print(
        "Response Length:",
        len(response.text)
    )

    print("")

    print(
        "Response awal:"
    )

    print(
        response.text[:2000]
    )

    print("")

    if response.status_code == 200:

        print(
            "SUCCESS:"
        )

        print(
            "GitHub Actions dapat mengakses "
            "website BMKG."
        )

    elif response.status_code == 403:

        print(
            "FAILED:"
        )

        print(
            "Server BMKG menolak request "
            "dengan HTTP 403."
        )

        print(
            "Kemungkinan besar masalah "
            "IP / WAF / Anti-Bot."
        )

    else:

        print(
            "WARNING:"
        )

        print(
            "Server memberikan HTTP status:",
            response.status_code
        )


except Exception as e:

    print("")

    print(
        "ERROR:"
    )

    print(
        e
    )
