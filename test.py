import re

text = """<tr><td><a href="/Archives/edgar/data/1067983/000119312526226661/53405.xml"><img class="img_icon" src="/icons/text.gif" alt="folder icon">53405.xml</a></td><td>45259</td><td>2026-05-15 16:06:05</td></tr>
<tr><td><a href="/Archives/edgar/data/1067983/000119312526226661/primary_doc.xml"><img class="img_icon" src="/icons/text.gif" alt="folder icon">primary_doc.xml</a></td><td>5555</td><td>2026-05-15 16:06:05</td></tr>"""

for line in text.splitlines():
    if ".xml" in line.lower() and "index" not in line.lower():
        match = re.search(r'href="([^"]+\.xml)"', line, re.IGNORECASE)
        print("Line:", line)
        print("Match:", match.group(1) if match else "None")
