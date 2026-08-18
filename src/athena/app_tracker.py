import os
import sqlite3
import json
import time
import datetime
import re

DB_PATH = os.path.join("data", "applications.db")

class ApplicationTracker:
    _instance = None

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: str = DB_PATH):
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    app_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    clean_title TEXT NOT NULL,
                    language TEXT,
                    periodicity TEXT,
                    state TEXT,
                    district TEXT,
                    applicant_name TEXT,
                    organization TEXT,
                    email TEXT,
                    phone TEXT,
                    submission_timestamp TEXT,
                    auto_probability REAL,
                    max_similarity REAL,
                    status TEXT,
                    admin_remarks TEXT,
                    reviewed_timestamp TEXT,
                    audit_json TEXT
                )
            """)
            conn.commit()

    def generate_app_id(self) -> str:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM applications")
            count = cursor.fetchone()[0] + 1
        return f"PRGI-2026-A{count:04d}"

    def submit_application(
        self,
        title: str,
        language: str,
        periodicity: str,
        state: str,
        district: str,
        applicant_name: str,
        organization: str,
        email: str,
        phone: str,
        audit_result: dict
    ) -> str:
        app_id = self.generate_app_id()
        clean_title = re.sub(r"[^\w\s]", " ", title.upper()).strip()
        clean_title = re.sub(r"\s+", " ", clean_title)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        auto_prob = audit_result.get("acceptance_probability", 0.0)
        max_sim = audit_result.get("highest_similarity", 0.0)
        
        # Initial status
        initial_status = "PENDING_REVIEW"
        if auto_prob >= 75.0 and audit_result.get("compliance", {}).get("is_compliant", True):
            initial_status = "AUTO_AUDITED_CLEAR"

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO applications (
                    app_id, title, clean_title, language, periodicity,
                    state, district, applicant_name, organization, email,
                    phone, submission_timestamp, auto_probability, max_similarity,
                    status, admin_remarks, reviewed_timestamp, audit_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_id, title, clean_title, language, periodicity,
                state, district, applicant_name, organization, email,
                phone, timestamp, auto_prob, max_sim,
                initial_status, "", "", json.dumps(audit_result)
            ))
            conn.commit()

        return app_id

    def get_application(self, app_id: str) -> dict:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE app_id = ? OR title LIKE ?", (app_id, f"%{app_id}%"))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("audit_json"):
                    try:
                        d["audit_data"] = json.loads(d["audit_json"])
                    except Exception:
                        d["audit_data"] = {}
                return d
            return None

    def get_all_applications(self) -> list:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications ORDER BY submission_timestamp DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def update_application_status(self, app_id: str, new_status: str, admin_remarks: str = "") -> bool:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE applications
                SET status = ?, admin_remarks = ?, reviewed_timestamp = ?
                WHERE app_id = ?
            """, (new_status, admin_remarks, timestamp, app_id))
            conn.commit()
            return cursor.rowcount > 0

    def check_prior_applications(self, proposed_title: str) -> list:
        """
        Queries live submitted applications to prevent duplicate title submissions
        from conflicting with prior in-progress or approved applications.
        """
        clean = re.sub(r"[^\w\s]", " ", proposed_title.upper()).strip()
        clean = re.sub(r"\s+", " ", clean)
        
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM applications
                WHERE status IN ('PENDING_REVIEW', 'AUTO_AUDITED_CLEAR', 'APPROVED')
            """)
            rows = cursor.fetchall()

        conflicts = []
        for r in rows:
            app_clean = r["clean_title"]
            if clean == app_clean or clean in app_clean or app_clean in clean:
                conflicts.append(dict(r))
        return conflicts
