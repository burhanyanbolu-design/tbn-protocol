"""Add /how-it-works route to server.py"""
F = "/opt/tbn-protocol/server.py"
with open(F) as fh:
    c = fh.read()

if "how_it_works" not in c:
    c += '''

@app.route("/how-it-works")
def how_it_works():
    return render_template("tbn_how_it_works.html")
'''
    with open(F, "w") as fh:
        fh.write(c)
    print("[+] Added /how-it-works route")
else:
    print("[=] Route already exists")
