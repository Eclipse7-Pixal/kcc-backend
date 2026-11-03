import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

PDF_PATH = "student_result.pdf"


@app.route("/", methods=["GET"])
def home():
  return jsonify(
      {
          "status": "online",
          "message": "ECLIPSE7 KCC Backend is running successfully!",
      }
  )


@app.route("/api/fetch-result", methods=["POST"])
def fetch_result():
  data = request.json or {}
  username = data.get("username")
  password = data.get("password")

  if not username or not password:
    return jsonify({"error": "Username and password are required"}), 400

  try:
    with sync_playwright() as p:
      browser = p.chromium.launch(
          headless=True,
          args=[
              "--no-sandbox",
              "--disable-setuid-sandbox",
              "--disable-dev-shm-usage",
              "--disable-gpu",
          ],
      )
      context = browser.new_context(viewport={"width": 1280, "height": 800})
      page = context.new_page()

      # Corrected to wait_until with underscore
      page.goto(
          "https://kcc-student.eduaakar.com/exam-sign-in",
          wait_until="networkidle",
      )
      page.fill('input[placeholder*="user name" i]', username)
      page.fill('input[placeholder*="password" i]', password)

      with page.expect_navigation(wait_until="networkidle"):
        page.click('button:has-text("Login")')

      if "exam-sign-in" in page.url:
        browser.close()
        return jsonify(
            {"error": "Invalid credentials or login failed. Please check."}
        ), 401

      if not page.url.endswith("/progress_report"):
        page.goto(
            "https://kcc-student.eduaakar.com/progress_report",
            wait_until="networkidle",
        )

      page.wait_for_timeout(2000)

      page.pdf(
          path=PDF_PATH,
          format="A3",
          print_background=True,
          margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
      )
      browser.close()

    return send_file(
        PDF_PATH,
        as_attachment=True,
        download_name=f"KCC_Result_{username}.pdf",
    )

  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
