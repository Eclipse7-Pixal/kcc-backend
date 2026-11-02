import os
import time
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)  # Enable CORS so your GitHub Pages frontend can talk to this backend

PDF_PATH = "student_result.pdf"


@app.route("/api/fetch-result", methods=["POST"])
def fetch_result():
  data = request.json
  username = data.get("username")
  password = data.get("password")

  if not username or not password:
    return jsonify({"error": "Username and password are required"}), 400

  try:
    with sync_playwright() as p:
      # Launch headless browser
      browser = p.chromium.launch(
          headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
      )
      context = browser.new_context(
          viewport={"width": 1280, "height": 800}
      )
      page = context.new_page()

      # 1. Navigate to KCC Login Page
      page.goto(
          "https://kcc-student.eduaakar.com/exam-sign-in",
          waitUntil="networkidle",
      )

      # 2. Input Credentials
      page.fill('input[placeholder*="user name" i]', username)
      page.fill('input[placeholder*="password" i]', password)

      # 3. Click Login Button & Wait for Navigation to Result/Progress Page
      with page.expect_navigation(waitUntil="networkidle"):
        page.click('button:has-text("Login")')

      # Check if login failed (e.g., error toast or still on login page)
      if "exam-sign-in" in page.url:
        browser.close()
        return jsonify(
            {"error": "Invalid credentials or login failed. Please check."}
        ), 401

      # 4. Navigate or wait for progress/result section
      # Based on your portal screenshot, it redirects to /progress_report
      if not page.url.endswith("/progress_report"):
        page.goto(
            "https://kcc-student.eduaakar.com/progress_report",
            waitUntil="networkidle",
        )

      # Optional delay to ensure charts/graphs load completely
      page.wait_for_timeout(2000)

      # 5. Print to PDF configured for A3 layout
      page.pdf(
          path=PDF_PATH,
          format="A3",
          print_background=True,
          margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
      )

      browser.close()

    # Send the generated PDF back to the user
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
