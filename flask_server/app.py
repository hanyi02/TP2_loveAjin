from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# =========================================================
# MariaDB 접속 정보
# password만 본인 MariaDB 비밀번호로 수정
# 비밀번호가 없으면 password="" 로 둔다.
# =========================================================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "love_ajin",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def ok(data=None, message="success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    })


def fail(error, status_code=500):
    return jsonify({
        "success": False,
        "error": str(error)
    }), status_code


@app.route("/", methods=["GET"])
def home():
    return ok({
        "server": "Love Ajin Flask API",
        "routes": [
            "/api/test",
            "/api/characters",
            "/api/save_day",
            "/api/save_ending",
            "/api/load/<save_id>"
        ]
    }, "server running")


@app.route("/api/test", methods=["GET"])
def test_server():
    return ok({"server": "running", "db": DB_CONFIG["database"]}, "Flask server is running")


@app.route("/api/characters", methods=["GET"])
def get_characters():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM male_character ORDER BY male_id")
            rows = cur.fetchall()
        return ok(rows, "characters loaded")
    except Exception as e:
        return fail(e)
    finally:
        conn.close()


def normalize_save_id(raw_save_id):
    """
    Ren'Py에서 첫 저장 시 save_id=None 또는 ""로 보내면 새 save_id를 발급한다.
    이미 발급된 save_id가 있으면 숫자로 변환해서 기존 저장 슬롯을 갱신한다.
    """
    if raw_save_id is None:
        return None

    if raw_save_id == "":
        return None

    if raw_save_id == 0 or raw_save_id == "0":
        return None

    return int(raw_save_id)


@app.route("/api/save_day", methods=["POST"])
def save_day():
    data = request.get_json(force=True)

    save_id = normalize_save_id(data.get("save_id"))
    player = data.get("player", {})
    status = data.get("status", {})
    affection = data.get("affection", {})
    inventory = data.get("inventory", {})
    action_log = data.get("action_log", [])

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # 1. 플레이어 현재 상태 저장
            # save_id가 없으면 AUTO_INCREMENT로 신규 발급
            if save_id is None:
                cur.execute(
                    """
                    INSERT INTO player_save
                    (player_name, current_day, gold, hp, charm, intelligence, stress)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        player.get("name", "아진"),
                        int(player.get("current_date", 1)),
                        int(player.get("gold", 0)),
                        int(status.get("hp", 0)),
                        int(status.get("charm", 0)),
                        int(status.get("intelligence", 0)),
                        int(status.get("stress", 0)),
                    )
                )
                save_id = cur.lastrowid

            # save_id가 있으면 기존 저장 슬롯 갱신
            else:
                cur.execute(
                    """
                    INSERT INTO player_save
                    (save_id, player_name, current_day, gold, hp, charm, intelligence, stress)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        player_name = VALUES(player_name),
                        current_day = VALUES(current_day),
                        gold = VALUES(gold),
                        hp = VALUES(hp),
                        charm = VALUES(charm),
                        intelligence = VALUES(intelligence),
                        stress = VALUES(stress)
                    """,
                    (
                        save_id,
                        player.get("name", "아진"),
                        int(player.get("current_date", 1)),
                        int(player.get("gold", 0)),
                        int(status.get("hp", 0)),
                        int(status.get("charm", 0)),
                        int(status.get("intelligence", 0)),
                        int(status.get("stress", 0)),
                    )
                )

            # 2. 현재 save_id의 세부 데이터는 최신 상태로 다시 저장
            cur.execute("DELETE FROM affection_save WHERE save_id = %s", (save_id,))
            cur.execute("DELETE FROM inventory_save WHERE save_id = %s", (save_id,))
            cur.execute("DELETE FROM action_log WHERE save_id = %s", (save_id,))

            # 3. 남주별 호감도 저장
            for male_id, score in affection.items():
                cur.execute(
                    """
                    INSERT INTO affection_save
                    (save_id, male_id, affection)
                    VALUES (%s, %s, %s)
                    """,
                    (save_id, int(male_id), int(score))
                )

            # 4. 인벤토리 저장
            for item_id, item_count in inventory.items():
                cur.execute(
                    """
                    INSERT INTO inventory_save
                    (save_id, item_id, item_count)
                    VALUES (%s, %s, %s)
                    """,
                    (save_id, int(item_id), int(item_count))
                )

            # 5. 행동 로그 저장
            for log in action_log:
                cur.execute(
                    """
                    INSERT INTO action_log
                    (save_id, day, action_name)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        save_id,
                        int(log.get("day", 0)),
                        str(log.get("action_name", ""))
                    )
                )

        conn.commit()
        return jsonify({
            "success": True,
            "message": "day saved",
            "save_id": save_id,
            "data": {
                "save_id": save_id
            }
        })

    except Exception as e:
        conn.rollback()
        return fail(e)

    finally:
        conn.close()


@app.route("/api/save_ending", methods=["POST"])
def save_ending():
    data = request.get_json(force=True)

    save_id = normalize_save_id(data.get("save_id"))

    if save_id is None:
        return fail("save_id가 없습니다. 엔딩 저장 전에 /api/save_day가 먼저 성공해야 합니다.", 400)

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ending_log
                (save_id, ending_id, best_male_id, highest_score,
                 final_charm, final_intelligence, final_stress)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    save_id,
                    int(data["ending_id"]),
                    int(data["best_male_id"]),
                    int(data["highest_score"]),
                    int(data["final_charm"]),
                    int(data["final_intelligence"]),
                    int(data["final_stress"]),
                )
            )

        conn.commit()
        return ok({"save_id": save_id}, "ending saved")

    except Exception as e:
        conn.rollback()
        return fail(e)

    finally:
        conn.close()


@app.route("/api/load/<int:save_id>", methods=["GET"])
def load_game(save_id):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM player_save WHERE save_id = %s", (save_id,))
            player_row = cur.fetchone()

            if not player_row:
                return ok(None, "no save data")

            cur.execute("SELECT male_id, affection FROM affection_save WHERE save_id = %s", (save_id,))
            affection_rows = cur.fetchall()

            cur.execute("SELECT item_id, item_count FROM inventory_save WHERE save_id = %s", (save_id,))
            inventory_rows = cur.fetchall()

            cur.execute("SELECT day, action_name FROM action_log WHERE save_id = %s ORDER BY log_id", (save_id,))
            action_rows = cur.fetchall()

        result = {
            "player": {
                "name": player_row["player_name"],
                "gold": player_row["gold"],
                "current_date": player_row["current_day"],
            },
            "status": {
                "hp": player_row["hp"],
                "charm": player_row["charm"],
                "intelligence": player_row["intelligence"],
                "stress": player_row["stress"],
            },
            "affection": {str(row["male_id"]): row["affection"] for row in affection_rows},
            "inventory": {str(row["item_id"]): row["item_count"] for row in inventory_rows},
            "action_log": action_rows,
        }

        return ok(result, "save loaded")

    except Exception as e:
        return fail(e)

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
