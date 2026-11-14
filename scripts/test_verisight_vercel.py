import urllib.request
import re

url = "https://verisight-p7ke.vercel.app"
print(f"Testing real Vercel URL: {url}")

try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("HTTP Status:", resp.status)
        html = resp.read().decode("utf-8")
        js_files = re.findall(r'src="(/assets/[^"]+\.js)"', html)
        print("JS bundles found:", js_files)
        for js in js_files:
            js_url = url + js
            content = urllib.request.urlopen(js_url).read().decode("utf-8")
            render_matches = re.findall(r'https://[a-zA-Z0-9\.\-_/]*render[a-zA-Z0-9\.\-_/]*', content)
            print("Render URLs in bundle:", set(render_matches))
            # Check if updated progress code is present in bundle
            if "Computing optical quality assessment" in content:
                print("Latest progress pipeline code is DEPLOYED!")
            else:
                print("Bundle does not contain the newest commit yet (might be building).")
except Exception as e:
    print("Error:", e)

