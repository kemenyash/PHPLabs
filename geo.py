import psycopg2
import requests
import json
import time

# --- Налаштування бази даних ---
DB_NAME = "ukraine_geo"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# --- Створення таблиць ---
def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE EXTENSION IF NOT EXISTS postgis;

            CREATE TABLE IF NOT EXISTS regions (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS districts (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                region_id INT REFERENCES regions(id),
                code TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settlements (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                district_id INT REFERENCES districts(id),
                type TEXT,
                code TEXT UNIQUE NOT NULL,
                region_name TEXT,
                district_name TEXT
            );

            CREATE TABLE IF NOT EXISTS streets (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                settlement_id INT REFERENCES settlements(id)
            );

            CREATE TABLE IF NOT EXISTS buildings (
                id SERIAL PRIMARY KEY,
                street_id INT REFERENCES streets(id),
                house_number TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                location GEOMETRY(Point, 4326)
            );
        """)
        conn.commit()
        print("✅ Таблиці створено.")

# --- Імпорт КАТОТТГ з JSON ---
def import_katottg_json(conn, path="katottg.json"):
    settlements = set()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    with conn.cursor() as cur:
        for item in data["items"]:
            level1 = (item.get("level1") or "").strip()
            level2 = (item.get("level2") or "").strip()
            level3 = (item.get("level3") or "").strip()
            level4 = (item.get("level4") or "").strip()
            code = level4 or level3 or level2 or level1 or ""
            name = (item.get("name") or "").strip()
            category = (item.get("category") or "").strip()
            settlements.add(name)

            try:
                if level1:
                    cur.execute("""
                        INSERT INTO regions (name, code)
                        VALUES (%s, %s)
                        ON CONFLICT (code) DO NOTHING
                    """, (level1, level1))

                if level2:
                    cur.execute("SELECT id FROM regions WHERE code = %s", (level1,))
                    region_id = cur.fetchone()
                    if region_id:
                        cur.execute("""
                            INSERT INTO districts (name, code, region_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (code) DO NOTHING
                        """, (level2, level2, region_id[0]))

                if level3:
                    cur.execute("SELECT id FROM districts WHERE code = %s", (level2,))
                    district_id = cur.fetchone()
                    if district_id:
                        cur.execute("""
                            INSERT INTO settlements (name, type, code, district_id, region_name, district_name)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (code) DO NOTHING
                        """, (name, category, code, district_id[0], level1, level2))
            except Exception as ex:
                print(f"⚠️ Помилка імпорту {name} ({code}): {ex}")

    conn.commit()
    print("✅ КАТОТТГ JSON імпортовано.")
    return list(settlements)

# --- Отримання будинків з OSM ---
def fetch_osm_buildings(settlement_name):
    query = f"""
    [out:json][timeout:60];
    area["name"="{settlement_name}"]->.searchArea;
    (
      way["building"](area.searchArea);
    );
    out center tags;
    """
    url = "http://overpass-api.de/api/interpreter"
    try:
        response = requests.post(url, data={'data': query})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Помилка запиту OSM для {settlement_name}: {response.status_code}")
            return {"elements": []}
    except Exception as e:
        print(f"⚠️ Виняток запиту OSM для {settlement_name}: {e}")
        return {"elements": []}

# --- Імпорт будинків ---
def import_osm_buildings(conn, osm_data, settlement_name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM settlements WHERE name ILIKE %s", (settlement_name,))
        settlement = cur.fetchone()
        if not settlement:
            print(f"❌ Населений пункт '{settlement_name}' не знайдено в базі.")
            return
        settlement_id = settlement[0]

        inserted = 0
        for el in osm_data["elements"]:
            if "center" not in el or "tags" not in el:
                continue

            lat = el["center"]["lat"]
            lon = el["center"]["lon"]
            tags = el["tags"]
            street = tags.get("addr:street", "Невідома")
            house = tags.get("addr:housenumber", "без номера")

            cur.execute("SELECT id FROM streets WHERE name = %s AND settlement_id = %s", (street, settlement_id))
            res = cur.fetchone()
            if res:
                street_id = res[0]
            else:
                cur.execute("INSERT INTO streets (name, settlement_id) VALUES (%s, %s) RETURNING id", (street, settlement_id))
                street_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO buildings (street_id, house_number, latitude, longitude, location)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """, (street_id, house, lat, lon, lon, lat))
            inserted += 1

        conn.commit()
        print(f"✅ {inserted} будинків імпортовано для: {settlement_name}")

# --- Основна функція ---
def main():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    create_tables(conn)
    settlements = import_katottg_json(conn, "katottg.json")

    for name in settlements:
        print(f"🌍 Обробка: {name}")
        osm_data = fetch_osm_buildings(name)
        import_osm_buildings(conn, osm_data, name)
        time.sleep(2)

    conn.close()

if __name__ == "__main__":
    main()
