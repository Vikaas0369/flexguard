import mimetypes
import sqlite3
from pathlib import Path

import httpx


QUEUE_DB = Path("offline_queue.db")

API_URL = "http://127.0.0.1:8000"

MAX_RETRIES = 3


def get_connection():
    return sqlite3.connect(QUEUE_DB)


def create_queue_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            inspector TEXT NOT NULL,
            finding TEXT NOT NULL,
            notes TEXT,
            risk_level TEXT NOT NULL,
            evidence_path TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            retry_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    connection.commit()
    connection.close()


def add_to_queue(
    location,
    inspector,
    finding,
    notes,
    risk_level,
    evidence_path=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO offline_queue (
            location,
            inspector,
            finding,
            notes,
            risk_level,
            evidence_path,
            status,
            retry_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            location,
            inspector,
            finding,
            notes,
            risk_level,
            evidence_path,
            "PENDING",
            0
        )
    )

    queue_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return queue_id


def get_pending_inspections():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM offline_queue
        WHERE status = 'PENDING'
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def mark_synced(queue_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE offline_queue
        SET status = 'SYNCED'
        WHERE id = ?
        """,
        (queue_id,)
    )

    connection.commit()
    connection.close()


def record_failed_retry(queue_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT retry_count
        FROM offline_queue
        WHERE id = ?
        """,
        (queue_id,)
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return

    new_retry_count = row[0] + 1

    if new_retry_count >= MAX_RETRIES:
        new_status = "FAILED"
    else:
        new_status = "PENDING"

    cursor.execute(
        """
        UPDATE offline_queue
        SET retry_count = ?,
            status = ?
        WHERE id = ?
        """,
        (
            new_retry_count,
            new_status,
            queue_id
        )
    )

    connection.commit()
    connection.close()


def sync_pending_inspections():

    pending = get_pending_inspections()

    if not pending:
        print("No pending inspections.")
        return

    for inspection in pending:

        queue_id = inspection[0]
        location = inspection[1]
        inspector = inspection[2]
        finding = inspection[3]
        notes = inspection[4]
        risk_level = inspection[5]
        evidence_path = inspection[6]

        data = {
            "location": location,
            "inspector": inspector,
            "finding": finding,
            "notes": notes,
            "risk_level": risk_level,
        }

        try:
            response = httpx.post(
                f"{API_URL}/inspections",
                json=data,
                timeout=10
            )

            if response.status_code != 200:
                record_failed_retry(queue_id)

                print(
                    f"Queue {queue_id}: create failed"
                )

                continue

            server_inspection = response.json()

            inspection_id = server_inspection["id"]

            if evidence_path:
                file_path = Path(evidence_path)

                if file_path.exists():

                    mime_type, _ = mimetypes.guess_type(
                        file_path.name
                    )

                    if mime_type is None:
                        mime_type = "application/octet-stream"

                    with open(
                        file_path,
                        "rb"
                    ) as image_file:

                        files = {
                            "file": (
                                file_path.name,
                                image_file,
                                mime_type
                            )
                        }

                        upload_response = httpx.post(
                            (
                                f"{API_URL}/inspections/"
                                f"{inspection_id}/evidence"
                            ),
                            files=files,
                            timeout=20
                        )

                    if upload_response.status_code != 200:
                        record_failed_retry(queue_id)

                        print(
                            f"Queue {queue_id}: "
                            "evidence upload failed"
                        )

                        continue

            submit_response = httpx.post(
                (
                    f"{API_URL}/inspections/"
                    f"{inspection_id}/submit"
                ),
                timeout=10
            )

            if submit_response.status_code != 200:
                record_failed_retry(queue_id)

                print(
                    f"Queue {queue_id}: submit failed"
                )

                continue

            mark_synced(queue_id)

            print(
                f"Queue {queue_id}: SYNCED"
            )

        except Exception:
            record_failed_retry(queue_id)

            print(
                f"Queue {queue_id}: retry failed"
            )


create_queue_table()


if __name__ == "__main__":
    sync_pending_inspections()