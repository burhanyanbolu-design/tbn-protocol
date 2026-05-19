"""Add prospects blueprint to server.py"""

with open("server.py", "r") as f:
    content = f.read()

# Add import
old_import = "from api.compliance_drift import compliance_drift"
new_import = old_import + "\nfrom api.prospects import prospects_bp"

if "prospects_bp" not in content:
    content = content.replace(old_import, new_import)

# Add blueprint registration
old_register = 'app.register_blueprint(compliance_drift, url_prefix="/api/compliance")'
new_register = old_register + '\napp.register_blueprint(prospects_bp)'

if "prospects_bp" not in content:
    content = content.replace(old_register, new_register)

with open("server.py", "w") as f:
    f.write(content)

print("Done — prospects blueprint added to server.py")
