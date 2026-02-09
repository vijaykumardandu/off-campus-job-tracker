import os
import requests
from datetime import date
from flask import Flask, render_template, request, redirect, flash
from database import connect_db
from ai_engine.resume_parser import extract_resume_text
from ai_engine.job_matcher import calculate_match_score

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    jobs = []

    if request.method == "POST":
        keyword = request.form.get("keyword")

        try:
            with open("resume_text.txt", "r", encoding="utf-8") as f:
                resume_text = f.read()
        except FileNotFoundError:
            resume_text = ""

        url = f"https://remotive.com/api/remote-jobs?search={keyword}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json() if response.status_code == 200 else {}
        except Exception:
            data = {}

        for job in data.get("jobs", [])[:10]:
            description = job.get("description", "")
            score = calculate_match_score(resume_text, description)

            jobs.append({
                "title": job.get("title"),
                "company": job.get("company_name"),
                "url": job.get("url"),
                "score": score
            })

        jobs.sort(key=lambda x: x["score"], reverse=True)

    return render_template("dashboard.html", jobs=jobs)


# ---------------- SAVE JOB ----------------
@app.route("/save", methods=["POST"])
def save_job():
    title = request.form.get("title")
    company = request.form.get("company")
    link = request.form.get("link")
    score = request.form.get("score")

    today = date.today().strftime("%Y-%m-%d")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM applications WHERE title = ? AND company = ?",
        (title, company)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO applications (title, company, link, score, status, date_applied)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, company, link, score, "Applied", today)
        )
        conn.commit()

    conn.close()
    flash("Job saved successfully!", "success")
    return redirect("/")


# ---------------- APPLICATIONS ----------------
@app.route("/applications", methods=["GET", "POST"])
def applications():
    conn = connect_db()
    cursor = conn.cursor()

    keyword = request.form.get("keyword", "")
    status = request.form.get("status", "")

    query = """
        SELECT id, title, company, link, score, status, date_applied
        FROM applications
        WHERE (title LIKE ? OR company LIKE ?)
    """
    params = [f"%{keyword}%", f"%{keyword}%"]

    if status:
        query += " AND status = ?"
        params.append(status)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    jobs = [{
        "id": r[0],
        "title": r[1],
        "company": r[2],
        "link": r[3],
        "score": r[4],
        "status": r[5],
        "date": r[6]
    } for r in rows]

    return render_template("applications.html", jobs=jobs, keyword=keyword, status=status)


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status", methods=["POST"])
def update_status():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (request.form["status"], request.form["job_id"])
    )

    conn.commit()
    conn.close()
    return redirect("/applications")


# ---------------- DELETE JOB ----------------
@app.route("/delete_job", methods=["POST"])
def delete_job():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM applications WHERE id = ?", (request.form["job_id"],))
    conn.commit()
    conn.close()

    flash("Job deleted successfully!", "error")
    return redirect("/applications")


# ---------------- ANALYTICS ----------------
@app.route("/analytics")
def analytics():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'")
    applied = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status='Interview'")
    interview = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "analytics.html",
        total=total,
        applied=applied,
        interview=interview,
        rejected=rejected
    )


# ---------------- UPLOAD RESUME ----------------
@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        file = request.files.get("resume")

        if file and file.filename:
            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)

            text = extract_resume_text(path)

            with open("resume_text.txt", "w", encoding="utf-8") as f:
                f.write(text)

            return render_template("upload_resume.html", message="Resume uploaded successfully!")

    return render_template("upload_resume.html")


# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

