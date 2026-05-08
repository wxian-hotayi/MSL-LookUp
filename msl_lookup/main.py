"""MSL Lookup Tool - Optimized version using DigiKey API."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from local_db import cache_msl, get_cached_msl, init_db
from digikey_api import search_part_retry as digikey_search, DigiKeyAPIError


class MSLGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MSL Lookup Tool - DigiKey + Mouser")
        self.root.geometry("650x550")

        self.df = None
        self.mpn_msl_map = {}
        self.start_time = None

        self._setup_ui()
        init_db()

    def _setup_ui(self):
        # File selection
        file_frame = ttk.LabelFrame(self.root, text="Input Excel File (.xlsx)", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.file_path_var = tk.StringVar(value="No file selected")
        ttk.Label(file_frame, textvariable=self.file_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(side="right")

        # Action button
        action_frame = ttk.Frame(self.root)
        action_frame.pack(pady=10)

        self.start_btn = ttk.Button(action_frame, text="Start MSL Lookup", command=self._start_lookup, width=20)
        self.start_btn.pack()

        # Progress frame with details
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding=10)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=5)

        # Progress details
        self.progress_detail_var = tk.StringVar(value="0 / 0  |  Elapsed: 0s  |  ETA: --")
        ttk.Label(progress_frame, textvariable=self.progress_detail_var, font=("Courier", 10)).pack()

        self.status_var = tk.StringVar(value="Ready - Select an Excel file to begin")
        ttk.Label(self.root, textvariable=self.status_var).pack()

        # Preview Treeview
        preview_frame = ttk.LabelFrame(self.root, text="Preview (MPN & MSL)", padding=10)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.preview_tree = ttk.Treeview(preview_frame, columns=("MPN", "MSL", "Source"), show="headings", height=10)
        self.preview_tree.heading("MPN", text="MPN")
        self.preview_tree.heading("MSL", text="MSL")
        self.preview_tree.heading("Source", text="Source")
        self.preview_tree.column("MPN", width=280)
        self.preview_tree.column("MSL", width=80)
        self.preview_tree.column("Source", width=80)
        self.preview_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.preview_tree.configure(yscrollcommand=scrollbar.set)

        # Export button
        export_frame = ttk.Frame(self.root)
        export_frame.pack(pady=5)

        self.export_btn = ttk.Button(export_frame, text="Export to Excel", command=self._export_to_excel, width=20)
        self.export_btn.pack()

        # Output path
        output_frame = ttk.LabelFrame(self.root, text="Output File", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)

        self.output_path_var = tk.StringVar(value="Same as input (_with_msl.xlsx)")
        ttk.Label(output_frame, textvariable=self.output_path_var).pack(side="left", fill="x", expand=True)

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self.file_path_var.set(path)
            self._generate_output_path(path)
            self.status_var.set(f"Selected: {Path(path).name}")

    def _generate_output_path(self, input_path):
        p = Path(input_path)
        self.output_path = str(p.parent / f"{p.stem}_with_msl{p.suffix}")
        self.output_path_var.set(self.output_path)

    def _start_lookup(self):
        input_path = self.file_path_var.get()
        if input_path == "No file selected" or not input_path:
            messagebox.showwarning("No File", "Please select an Excel file first.")
            return

        try:
            self.df = pd.read_excel(input_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{str(e)}")
            return

        mpn_col = next((c for c in self.df.columns if str(c).lower() in ("mpn", "part number", "partno", "part")), None)
        if mpn_col is None:
            mpn_col = next((c for c in self.df.columns if "mpn" in str(c).lower() or ("part" in str(c).lower() and "number" in str(c).lower())), None)

        if mpn_col is None:
            messagebox.showerror("Error", f"Could not find MPN column.\nAvailable columns: {list(self.df.columns)}")
            return

        self._lookup_worker(mpn_col)

    def _lookup_worker(self, mpn_col):
        self.start_btn.config(state="disabled")
        self.progress_var.set(0)
        self.start_time = time.time()
        self.status_var.set("Looking up MSL...")

        mpns = self.df[mpn_col].dropna().astype(str).str.strip().str.replace(r'\s+', '', regex=True).tolist()

        thread = threading.Thread(target=self._lookup_thread, args=(mpns,))
        thread.start()

    def _lookup_thread(self, mpns):
        self.mpn_msl_map = {}
        total = len(mpns)
        lock = threading.Lock()
        counters = {"digikey": 0, "mouser": 0, "cache": 0, "done": 0}
        last_ui_update = [0.0]

        # Cache pass first (fast, no network)
        api_mpns = []
        for mpn in mpns:
            mpn_clean = mpn.strip()
            if not mpn_clean:
                counters["done"] += 1
                continue
            cached = get_cached_msl(mpn_clean.upper())
            if cached and cached[0]:
                self.mpn_msl_map[mpn] = (cached[0], "cache")
                counters["cache"] += 1
                counters["done"] += 1
            else:
                api_mpns.append(mpn)

        def lookup_one(mpn):
            try:
                r = digikey_search(mpn.strip())
                if r and r.get("msl"):
                    return mpn, r["msl"], "DigiKey", r
            except DigiKeyAPIError:
                pass
            return mpn, None, None, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(lookup_one, mpn): mpn for mpn in api_mpns}

            for future in as_completed(futures):
                mpn, msl, source, result = future.result()

                with lock:
                    self.mpn_msl_map[mpn] = (msl, source or "")
                    if source == "DigiKey":
                        counters["digikey"] += 1
                    counters["done"] += 1
                    current = counters["done"]
                    now = time.time()
                    elapsed = now - self.start_time
                    do_update = (now - last_ui_update[0] >= 0.2) or (current == total)
                    if do_update:
                        last_ui_update[0] = now
                        pct = current / total * 100
                        eta = (elapsed / current) * (total - current) if current > 0 else 0

                if msl and result:
                    cache_msl(mpn.strip().upper(), str(msl), "", result.get("manufacturer", ""), "")

                if do_update:
                    self.root.after(0, lambda c=current, t=total, e=elapsed, et=eta, p=pct:
                                   self._update_progress(c, t, e, et, p))

        self.root.after(0, lambda: self._lookup_complete(
            counters["digikey"], counters["mouser"], counters["cache"], total))

    def _update_progress(self, current, total, elapsed, eta, pct):
        self.progress_var.set(pct)
        eta_str = f"{int(eta)}s" if eta > 0 else "--"
        self.progress_detail_var.set(f"{current} / {total}  |  Elapsed: {int(elapsed)}s  |  ETA: {eta_str}")

    def _lookup_complete(self, digikey_hits, mouser_hits, cache_hits, total):
        self.progress_var.set(100)
        found = sum(1 for v in self.mpn_msl_map.values() if v[0])
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.status_var.set(f"Done! Found MSL for {found}/{total} parts in {int(elapsed)}s | DK:{digikey_hits} Mouser:{mouser_hits} Cache:{cache_hits}")

        self.preview_tree.delete(*self.preview_tree.get_children())
        for mpn, (msl, source) in self.mpn_msl_map.items():
            self.preview_tree.insert("", "end", values=(mpn, msl or "", source))

        self.start_btn.config(state="normal")

    def _export_to_excel(self):
        if not self.mpn_msl_map:
            messagebox.showwarning("No Data", "Please run MSL lookup first.")
            return

        result_df = pd.DataFrame({
            "MPN": list(self.mpn_msl_map.keys()),
            "MSL": [v[0] for v in self.mpn_msl_map.values()],
            "Source": [v[1] for v in self.mpn_msl_map.values()],
        })

        try:
            result_df.to_excel(self.output_path, index=False)
            messagebox.showinfo("Success", f"Results saved to:\n{self.output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MSLGUI(root)
    root.mainloop()
