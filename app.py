from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_FILE = "devices.db"

# DB 초기화 (기기별 최신 상태를 저장하는 테이블)
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS device_status (
            device_id TEXT PRIMARY KEY,
            status TEXT,
            battery TEXT,
            last_updated TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 1. 모바일 앱에서 상태를 전송받는 API
@app.route("/status", methods=["POST"])
def status_update():
    device_id = request.form.get("deviceId", "unknown")
    status = request.form.get("status", "?")
    battery = request.form.get("battery", "?")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 이미 있는 기기면 업데이트, 새로운 기기면 추가 (100대 관리용)
    c.execute('''
        INSERT INTO device_status (device_id, status, battery, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(device_id) DO UPDATE SET
        status=excluded.status,
        battery=excluded.battery,
        last_updated=excluded.last_updated
    ''', (device_id, status, battery, now))
    conn.commit()
    conn.close()

    return jsonify({"result": "OK", "deviceId": device_id})

# 2. 관리자 화면에 데이터를 제공하는 API
@app.route("/api/devices", methods=["GET"])
def get_devices():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT device_id, status, battery, last_updated FROM device_status ORDER BY last_updated DESC")
    rows = c.fetchall()
    conn.close()

    devices = []
    for row in rows:
        devices.append({
            "deviceId": row[0],
            "status": row[1],
            "battery": row[2],
            "lastUpdated": row[3]
        })
    return jsonify(devices)

# 3. 관리자 웹 화면 접속 라우트
@app.route("/admin")
def admin_page():
    return render_template("admin.html")

if __name__ == "__main__":
    # 외부 접속을 위해 0.0.0.0 사용
    app.run(host="0.0.0.0", port=5000)