"""Fix the broken how-it-works route in server.py"""
F = "/opt/tbn-protocol/server.py"
with open(F) as fh:
    lines = fh.readlines()

# Remove the broken lines at the end
while lines and ('how-it-works' in lines[-1] or 'how_it_works' in lines[-1] or 'tbn_how_it_works' in lines[-1] or lines[-1].strip() == ''):
    lines.pop()

# Add the correct route
lines.append('\n')
lines.append('@app.route("/how-it-works")\n')
lines.append('def how_it_works():\n')
lines.append('    return render_template("tbn_how_it_works.html")\n')

with open(F, 'w') as fh:
    fh.writelines(lines)

print("[OK] Fixed how-it-works route")
