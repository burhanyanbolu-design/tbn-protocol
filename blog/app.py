import json
import os
from datetime import datetime
from flask import Flask, request, redirect, session, Response

app = Flask(__name__)
app.secret_key = "hardin-blog-2026"
POSTS_FILE = "/var/www/blog/posts.json"
BLOG_HTML = "/var/www/blog/index.html"
ADMIN_PASSWORD = "Hardin2026"


def load_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE) as f:
        return json.load(f)


def save_posts(posts):
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, indent=2)
    rebuild_blog(posts)


def rebuild_blog(posts):
    cards = ""
    for p in posts:
        cards += (
            '<div class="post-card">'
            '<span class="post-tag">' + p["tag"] + "</span>"
            "<h2>" + p["title"] + "</h2>"
            "<p>" + p["summary"] + "</p>"
            '<div class="post-meta">' + p["date"] + " - Burhan Yanbolu - " + p["read_time"] + " min read</div>"
            "</div>"
        )

    if not cards:
        cards = '<p style="text-align:center;color:#6e7681;padding:80px;">No posts yet.</p>'

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Blog - Hardin AI Solutions</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-EF6RKG8KY2"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-EF6RKG8KY2");</script>
<style>
body{font-family:sans-serif;background:#0a0e1a;color:#c9d1d9;margin:0}
header{background:#0d1117;border-bottom:1px solid #21262d;padding:16px 40px;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:12px;text-decoration:none}
.hex{width:36px;height:36px;background:linear-gradient(135deg,#00d9ff,#0099cc);clip-path:polygon(30% 0%,70% 0%,100% 50%,70% 100%,30% 100%,0% 50%);display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:18px;color:#0d1117}
.logo-name{font-size:16px;font-weight:bold;color:#fff}
nav a{color:#58a6ff;text-decoration:none;margin-left:24px;font-size:14px}
.hero{padding:80px 40px;text-align:center;background:linear-gradient(135deg,#0d1117,#1a1f3a)}
.hero h1{font-size:48px;color:#fff;margin-bottom:16px}
.hero p{font-size:18px;color:#8b949e;max-width:600px;margin:0 auto}
.posts{max-width:900px;margin:60px auto;padding:0 40px}
.post-card{background:#0d1117;border:1px solid #21262d;border-radius:12px;padding:32px;margin-bottom:24px}
.post-tag{display:inline-block;background:#1f3a5f;color:#58a6ff;font-size:11px;padding:4px 10px;border-radius:12px;margin-bottom:12px}
.post-card h2{font-size:24px;color:#fff;margin-bottom:12px}
.post-card p{color:#8b949e;line-height:1.7;margin-bottom:16px}
.post-meta{font-size:12px;color:#6e7681}
footer{background:#0d1117;border-top:1px solid #21262d;padding:24px;text-align:center;margin-top:80px}
footer p{font-size:11px;color:#6e7681}
footer a{color:#58a6ff;text-decoration:none;margin:0 10px}
</style>
</head>
<body>
<header>
<a href="https://hardinai.co.uk" class="logo">
  <div class="hex">H</div>
  <span class="logo-name">HARDIN AI SOLUTIONS</span>
</a>
<nav>
  <a href="https://hardinai.co.uk">Home</a>
  <a href="https://tbn.hardinai.co.uk">TBN Protocol</a>
  <a href="https://blog.hardinai.co.uk">Blog</a>
  <a href="mailto:info@hardinai.co.uk">Contact</a>
</nav>
</header>
<div class="hero">
  <h1>Hardin AI Blog</h1>
  <p>Insights on AI agents, trust infrastructure, and AI for UK businesses</p>
</div>
<div class="posts">""" + cards + """</div>
<footer>
  <p>2026 Hardin Enterprises Ltd. All rights reserved.</p>
  <p style="margin-top:8px;">
    <a href="https://hardinai.co.uk">Home</a>
    <a href="https://tbn.hardinai.co.uk">TBN Protocol</a>
    <a href="mailto:info@hardinai.co.uk">Contact</a>
  </p>
</footer>
</body>
</html>"""

    with open(BLOG_HTML, "w") as f:
        f.write(html)


def login_page(error=""):
    err_html = ""
    if error:
        err_html = '<div style="background:#3a1a1a;border:1px solid #f85149;color:#f85149;padding:12px;border-radius:6px;margin-bottom:16px">' + error + "</div>"
    return """<!DOCTYPE html>
<html>
<head>
<title>Blog Admin Login</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#0a0e1a;color:#c9d1d9;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:32px;width:360px}
h2{color:#58a6ff;margin-bottom:20px}
input{width:100%;background:#161b22;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;padding:10px;font-size:14px;margin-bottom:12px}
.btn{background:#238636;color:#fff;border:none;border-radius:6px;padding:10px 20px;cursor:pointer;font-size:14px;font-weight:bold;width:100%}
</style>
</head>
<body>
<div class="card">
  <h2>Blog Admin Login</h2>
  """ + err_html + """
  <form method="POST" action="/admin/login">
    <input type="password" name="password" placeholder="Enter password" autofocus>
    <button class="btn">Login</button>
  </form>
</div>
</body>
</html>"""


def admin_page(posts, flash=""):
    flash_html = ""
    if flash:
        flash_html = '<div style="background:#1a3a2a;border:1px solid #3fb950;color:#3fb950;padding:12px;border-radius:6px;margin-bottom:16px">' + flash + "</div>"

    rows = ""
    for p in posts:
        rows += (
            '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid #21262d">'
            "<div>"
            '<b style="color:#fff">' + p["title"] + "</b><br>"
            '<small style="color:#6e7681">' + p["date"] + " - " + p["tag"] + "</small>"
            "</div>"
            '<form method="POST" action="/admin/delete/' + p["id"] + '" onsubmit="return confirm(\'Delete?\')">'
            '<button style="background:#b62324;color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer">Delete</button>'
            "</form>"
            "</div>"
        )

    if not rows:
        rows = '<p style="color:#6e7681">No posts yet.</p>'

    post_count = str(len(posts))

    return """<!DOCTYPE html>
<html>
<head>
<title>Blog Admin</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#0a0e1a;color:#c9d1d9}
header{background:#0d1117;border-bottom:1px solid #21262d;padding:16px 24px;display:flex;align-items:center;justify-content:space-between}
.c{max-width:800px;margin:40px auto;padding:0 24px}
.card{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:24px;margin-bottom:24px}
h2{color:#58a6ff;font-size:16px;margin-bottom:16px}
input,textarea{width:100%;background:#161b22;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;padding:10px;font-size:14px;margin-bottom:12px}
textarea{min-height:100px}
.btn{background:#238636;color:#fff;border:none;border-radius:6px;padding:10px 20px;cursor:pointer;font-size:14px;font-weight:bold}
</style>
</head>
<body>
<header>
  <b style="color:#58a6ff">HARDIN AI - Blog Admin</b>
  <a href="/admin/logout" style="color:#58a6ff;font-size:13px;text-decoration:none">Logout</a>
</header>
<div class="c">
  """ + flash_html + """
  <div class="card">
    <h2>Add New Post</h2>
    <form method="POST" action="/admin/add">
      <input name="title" placeholder="Title" required>
      <input name="tag" placeholder="Tag (e.g. TBN PROTOCOL)" required>
      <textarea name="summary" placeholder="Short summary"></textarea>
      <textarea name="content" placeholder="Full content"></textarea>
      <input name="read_time" placeholder="Read time (minutes)" value="5">
      <button class="btn">Publish</button>
    </form>
  </div>
  <div class="card">
    <h2>Posts (""" + post_count + """)</h2>
    """ + rows + """
  </div>
  <p style="text-align:center;font-size:12px;margin-top:16px">
    <a href="https://blog.hardinai.co.uk" target="_blank" style="color:#58a6ff">View blog</a>
  </p>
</div>
</body>
</html>"""


@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return Response(login_page(), mimetype="text/html")
    flash = request.args.get("flash", "")
    return Response(admin_page(load_posts(), flash=flash), mimetype="text/html")


@app.route("/admin/login", methods=["POST"])
def login():
    if request.form.get("password") == ADMIN_PASSWORD:
        session["logged_in"] = True
        return redirect("/admin")
    return Response(login_page(error="Wrong password"), mimetype="text/html")


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin")


@app.route("/admin/add", methods=["POST"])
def add_post():
    if not session.get("logged_in"):
        return redirect("/admin")
    posts = load_posts()
    posts.insert(0, {
        "id": str(int(datetime.now().timestamp())),
        "title": request.form["title"],
        "tag": request.form["tag"].upper(),
        "summary": request.form["summary"],
        "content": request.form["content"],
        "read_time": request.form.get("read_time", "5"),
        "date": datetime.now().strftime("%B %d, %Y"),
    })
    save_posts(posts)
    return redirect("/admin?flash=Post published!")


@app.route("/admin/delete/<post_id>", methods=["POST"])
def delete_post(post_id):
    if not session.get("logged_in"):
        return redirect("/admin")
    save_posts([p for p in load_posts() if p["id"] != post_id])
    return redirect("/admin?flash=Post deleted.")


if __name__ == "__main__":
    os.makedirs("/var/www/blog", exist_ok=True)
    app.run(host="0.0.0.0", port=5007)
