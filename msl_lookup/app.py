"""MSL Lookup Tool - Flask web server."""
import io
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from flask import Flask, Response, jsonify, render_template, request, send_file

from digikey_api import DigiKeyAPIError
from digikey_api import search_part_retry as digikey_search
from local_db import cache_msl, get_cached_msl, init_db

app = Flask(__name__)
jobs = {}

init_db()


def find_mpn_column(df):
    for candidate in ["MPN", "mpn", "Maker Part No", "Maker Part Number", "Part Number", "PartNo", "Part"]:
        if candidate in df.columns:
            return candidate
    for col in df.columns:
        s = str(col).lower()
        if "mpn" in s or ("part" in s and "number" in s):
            return col
    return None


def run_lookup(job_id, df, mpn_col):
    mpns = (
        df[mpn_col].dropna().astype(str)
        .apply(lambda x: re.sub(r"\s+", "", x.strip()))
        .tolist()
    )
    total = len(mpns)
    job = jobs[job_id]
    job.update({"status": "running", "total": total,
                "counters": {"digikey": 0, "cache": 0, "done": 0},
                "results": {}})
    results = job["results"]
    counters = job["counters"]
    lock = threading.Lock()

    # Cache pass first
    api_mpns = []
    for mpn in mpns:
        if not mpn:
            with lock:
                counters["done"] += 1
            continue
        cached = get_cached_msl(mpn.upper())
        if cached and cached[0]:
            results[mpn] = {"msl": cached[0], "source": "Cache", "manufacturer": cached[2] if len(cached) > 2 else ""}
            with lock:
                counters["cache"] += 1
                counters["done"] += 1
        else:
            api_mpns.append(mpn)

    def lookup_one(mpn):
        try:
            r = digikey_search(mpn)
            if r and r.get("msl"):
                return mpn, r["msl"], "DigiKey", r
        except DigiKeyAPIError:
            pass
        return mpn, None, None, None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(lookup_one, m): m for m in api_mpns}
        for future in as_completed(futures):
            mpn, msl, source, result = future.result()
            results[mpn] = {"msl": msl or "", "source": source or "Not Found", "manufacturer": result.get("manufacturer", "") if result else ""}
            with lock:
                if source == "DigiKey":
                    counters["digikey"] += 1
                counters["done"] += 1
            if msl and result:
                cache_msl(mpn.upper(), str(msl), "", result.get("manufacturer", ""), "")

    job["status"] = "done"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        df = pd.read_csv(f) if f.filename.endswith(".csv") else pd.read_excel(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "uploaded", "df": df, "total": len(df),
                    "counters": {}, "results": {}}
    return jsonify({
        "job_id": job_id,
        "columns": list(df.columns),
        "mpn_col": find_mpn_column(df),
        "total": len(df),
    })


@app.route("/api/lookup/<job_id>", methods=["POST"])
def start_lookup(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    mpn_col = (request.json or {}).get("mpn_col") or find_mpn_column(job["df"])
    if not mpn_col:
        return jsonify({"error": "MPN column not found"}), 400
    threading.Thread(target=run_lookup, args=(job_id, job["df"], mpn_col), daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/progress/<job_id>")
def progress(job_id):
    def stream():
        while True:
            job = jobs.get(job_id, {})
            c = job.get("counters", {})
            yield "data: {}\n\n".format(json.dumps({
                "done": c.get("done", 0),
                "total": job.get("total", 0),
                "status": job.get("status", "unknown"),
                "digikey": c.get("digikey", 0),
                "cache": c.get("cache", 0),
            }))
            if job.get("status") == "done":
                break
            time.sleep(0.3)

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/results/<job_id>")
def get_results(job_id):
    results = jobs.get(job_id, {}).get("results", {})
    return jsonify({"results": [
        {"mpn": mpn, "msl": v.get("msl", ""), "source": v.get("source", ""), "manufacturer": v.get("manufacturer", "")}
        for mpn, v in results.items()
    ]})


@app.route("/api/export/<job_id>")
def export(job_id):
    results = jobs.get(job_id, {}).get("results", {})
    if not results:
        return jsonify({"error": "No results"}), 400
    df = pd.DataFrame([
        {"MPN": k, "MSL": v.get("msl", ""), "Source": v.get("source", "")}
        for k, v in results.items()
    ])
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="msl_results.xlsx",
    )


@app.route("/api/search", methods=["POST"])
def search_single():
    mpn = re.sub(r"\s+", "", (request.json or {}).get("mpn", "").strip()).upper()
    if not mpn:
        return jsonify({"error": "MPN is required"}), 400

    cached = get_cached_msl(mpn)
    if cached and cached[0]:
        return jsonify({"mpn": mpn, "msl": cached[0], "source": "Cache"})

    try:
        result = digikey_search(mpn)
        if result and result.get("msl"):
            cache_msl(mpn, str(result["msl"]), "", result.get("manufacturer", ""), "")
            return jsonify({
                "mpn": mpn,
                "msl": result["msl"],
                "source": "DigiKey",
                "manufacturer": result.get("manufacturer", ""),
                "description": result.get("description", ""),
            })
    except DigiKeyAPIError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    return jsonify({"mpn": mpn, "msl": None, "source": "Not Found"})


if __name__ == "__main__":
    import webbrowser
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(port=5000, threaded=True)
