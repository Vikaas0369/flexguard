import mimetypes
import sqlite3
from pathlib import Path
from uuid import uuid4

import httpx


QUEUE_DB = Path("offline_queue.db")

API_URL = "http://127.0.0.1:9000"

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
            idempotency_key TEXT NOT NULL UNIQUE,
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
    evidence_path=None,
    idempotency_key=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    request_key = (
        idempotency_key
        or str(uuid4())
    )

    cursor.execute(
        """
        INSERT INTO offline_queue (
            idempotency_key,
            location,
            inspector,
            finding,
            notes,
            risk_level,
            evidence_path,
            status,
            retry_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_key,
            location,
            inspector,
            finding,
            notes,
            risk_level,
            evidence_path,
            "PENDING",
            0,
        ),
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


def get_queue_item(queue_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM offline_queue
        WHERE id = ?
        """,
        (queue_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "idempotency_key": row[1],
        "location": row[2],
        "inspector": row[3],
        "finding": row[4],
        "notes": row[5],
        "risk_level": row[6],
        "evidence_path": row[7],
        "status": row[8],
        "retry_count": row[9],
    }


def mark_synced(queue_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE offline_queue
        SET status = 'SYNCED'
        WHERE id = ?
        """,
        (queue_id,),
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
        (queue_id,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

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
            queue_id,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "retry_count": new_retry_count,
        "status": new_status,
    }


def sync_queue_item(queue_id):
    inspection = get_queue_item(
        queue_id
    )

    if inspection is None:
        return {
            "queue_id": queue_id,
            "status": "NOT_FOUND",
            "message": "Queue item does not exist",
        }

    if inspection["status"] != "PENDING":
        return {
            "queue_id": queue_id,
            "status": inspection["status"],
            "message": (
                "Queue item is not pending"
            ),
        }

    data = {
        "idempotency_key": (
            inspection["idempotency_key"]
        ),
        "location": inspection["location"],
        "inspector": inspection["inspector"],
        "finding": inspection["finding"],
        "notes": inspection["notes"],
        "risk_level": inspection["risk_level"],
    }

    try:
        response = httpx.post(
            f"{API_URL}/inspections",
            json=data,
            timeout=10,
        )

        if response.status_code != 200:
            retry = record_failed_retry(
                queue_id
            )

            return {
                "queue_id": queue_id,
                "status": retry["status"],
                "message": (
                    "Inspection creation failed"
                ),
            }

        server_inspection = response.json()

        inspection_id = (
            server_inspection["id"]
        )

        evidence_path = (
            inspection["evidence_path"]
        )

        if evidence_path:
            file_path = Path(
                evidence_path
            )

            # Do not claim SYNCED if expected
            # evidence has disappeared locally.
            if not file_path.exists():
                retry = record_failed_retry(
                    queue_id
                )

                return {
                    "queue_id": queue_id,
                    "status": retry["status"],
                    "message": (
                        "Evidence file is missing"
                    ),
                    "inspection_id": (
                        inspection_id
                    ),
                }

            mime_type, _ = (
                mimetypes.guess_type(
                    file_path.name
                )
            )

            if mime_type is None:
                mime_type = (
                    "application/octet-stream"
                )

            with open(
                file_path,
                "rb",
            ) as image_file:
                files = {
                    "file": (
                        file_path.name,
                        image_file,
                        mime_type,
                    )
                }

                upload_response = httpx.post(
                    (
                        f"{API_URL}/inspections/"
                        f"{inspection_id}/evidence"
                    ),
                    files=files,
                    timeout=20,
                )

            if upload_response.status_code != 200:
                retry = record_failed_retry(
                    queue_id
                )

                return {
                    "queue_id": queue_id,
                    "status": retry["status"],
                    "message": (
                        "Evidence upload failed: "
                        f"HTTP {upload_response.status_code} "
                        f"{upload_response.text}"
                    ),
                    "inspection_id": inspection_id,
                }

        submit_response = httpx.post(
            (
                f"{API_URL}/inspections/"
                f"{inspection_id}/submit"
            ),
            timeout=10,
        )

        if submit_response.status_code == 200:
            mark_synced(
                queue_id
            )

            return {
                "queue_id": queue_id,
                "status": "SYNCED",
                "message": (
                    "Inspection synchronized"
                ),
                "inspection_id": (
                    inspection_id
                ),
            }

        # Recovery case:
        # the server may already have submitted
        # the record even if the client previously
        # failed before updating its local state.
        check_response = httpx.get(
            (
                f"{API_URL}/inspections/"
                f"{inspection_id}"
            ),
            timeout=10,
        )

        if check_response.status_code == 200:
            server_record = (
                check_response.json()
            )

            if (
                server_record.get("status")
                == "submitted"
            ):
                mark_synced(
                    queue_id
                )

                return {
                    "queue_id": queue_id,
                    "status": "SYNCED",
                    "message": (
                        "Recovered existing "
                        "submitted inspection"
                    ),
                    "inspection_id": (
                        inspection_id
                    ),
                }

        retry = record_failed_retry(
            queue_id
        )

        return {
            "queue_id": queue_id,
            "status": retry["status"],
            "message": (
                "Inspection submission failed"
            ),
            "inspection_id": inspection_id,
        }

    except Exception as error:
        retry = record_failed_retry(
            queue_id
        )

        return {
            "queue_id": queue_id,
            "status": retry["status"],
            "message": str(error),
        }


def sync_pending_inspections():
    pending = get_pending_inspections()

    if not pending:
        print(
            "No pending inspections."
        )
        return []

    results = []

    for inspection in pending:
        queue_id = inspection[0]

        result = sync_queue_item(
            queue_id
        )

        results.append(
            result
        )

        print(
            f"Queue {queue_id}: "
            f"{result['status']} - "
            f"{result['message']}"
        )

    return results


create_queue_table()


if __name__ == "__main__":
    sync_pending_inspections()