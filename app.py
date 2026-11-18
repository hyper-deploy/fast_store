from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL থেকে number প্যারামিটারটি বের করা
        query_components = parse_qs(urlparse(self.path).query)
        phone_number = query_components.get('number', [None])[0]

        # ১. চেক করা নম্বর দেওয়া হয়েছে কিনা
        if not phone_number:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide ?number= parameter"}).encode())
            return

        # ২. নম্বরের ফরম্যাট ঠিক আছে কিনা
        if not phone_number.isdigit() and not (phone_number.startswith('+') and phone_number[1:].isdigit()):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid phone number format"}).encode())
            return

        try:
            url = "https://calltracer.in"
            headers = {
                "Host": "calltracer.in",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            payload = {
                "country": "IN",
                "q": phone_number
            }

            # calltracer.in-এ POST রিকোয়েস্ট
            response = requests.post(url, headers=headers, data=payload, timeout=10)

            if response.status_code != 200:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to fetch data. HTTP {response.status_code}"}).encode())
                return

            soup = BeautifulSoup(response.text, 'html.parser')

            # ডেটা এক্সট্রাক্ট করার ফাংশন
            def get_value(label):
                cell = soup.find(string=lambda t: t and label in t)
                if cell:
                    td = cell.find_parent("tr")
                    if td and td.find_all("td"):
                        tds = td.find_all("td")
                        if len(tds) > 1:
                            return tds[1].get_text(strip=True)
                return "N/A"

            data = {
                "Number": phone_number,
                "Complaints": get_value("Complaints"),
                "Owner Name": get_value("Owner Name"),
                "SIM Card": get_value("SIM card"),
                "Mobile State": get_value("Mobile State"),
                "IMEI Number": get_value("IMEI number"),
                "MAC Address": get_value("MAC address"),
                "Connection": get_value("Connection"),
                "IP Address": get_value("IP address"),
                "Owner Address": get_value("Owner Address"),
                "Hometown": get_value("Hometown"),
                "Reference City": get_value("Refrence City"),
                "Owner Personality": get_value("Owner Personality"),
                "Language": get_value("Language"),
                "Mobile Locations": get_value("Mobile Locations"),
                "Country": get_value("Country"),
                "Tracking History": get_value("Tracking History"),
                "Tracker ID": get_value("Tracker Id"),
                "Tower Locations": get_value("Tower Locations"),
            }

            # সব ফিল্ড N/A হলে (ডেটা না পেলে)
            if all(v == "N/A" for v in data.values()):
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No data found for this number."}).encode())
                return

            # সফলভাবে ডেটা পাওয়া গেলে
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
