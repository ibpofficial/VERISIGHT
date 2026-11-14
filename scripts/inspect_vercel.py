import urllib.request
import re

html = urllib.request.urlopen("https://ibptimebook.vercel.app").read().decode("utf-8")
js_files = re.findall(r'src="(/assets/[^"]+\.js)"', html)
print("JS files:", js_files)
for js in js_files:
    url = "https://ibptimebook.vercel.app" + js
    content = urllib.request.urlopen(url).read().decode("utf-8")
    render_matches = re.findall(r'https://[a-zA-Z0-9\.\-_/]*render[a-zA-Z0-9\.\-_/]*', content)
    print("Found render URLs in JS:", set(render_matches))
    # Look for baseURL or API_BASE
    base_match = re.findall(r'baseURL:\s*["\']([^"\']+)["\']', content)
    print("Found baseURL:", base_match)

