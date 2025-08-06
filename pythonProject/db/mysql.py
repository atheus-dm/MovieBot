import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

def search_by_keyword(keyword: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT f.film_id, f.title, f.release_year, f.length, f.rating, f.description,
GROUP_CONCAT(CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
FROM film f
LEFT JOIN film_actor fa ON f.film_id = fa.film_id
LEFT JOIN actor a ON fa.actor_id = a.actor_id
WHERE f.title LIKE %s OR f.description LIKE %s
GROUP BY f.film_id
    """
    cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        f"🎬 {r['title']} ({r['release_year']})\n"
        f"🕒 Длина: {r['length']} мин | 🏷️ Рейтинг: {r['rating']}\n"
        f"🎭 Актёры: {r['actors']}\n"
        f"📄 {r['description'][:300]}..."
        for r in results
    ]

def get_genres():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT category_id, name FROM category ORDER BY name")
    genres = cursor.fetchall()
    cursor.close()
    conn.close()
    return genres

def search_by_genre_year(genre_ids: list[int], year_from: int, year_to: int, offset: int = 0, limit: int = 10) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    genre_filter = ",".join([str(g) for g in genre_ids])
    query = f"""
        SELECT f.film_id, f.title, f.release_year, f.length, f.rating, f.description,
               GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genres,
               GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        JOIN film_actor fa ON f.film_id = fa.film_id
        JOIN actor a ON fa.actor_id = a.actor_id
        WHERE fc.category_id IN ({genre_filter})
          AND f.release_year BETWEEN %s AND %s
        GROUP BY f.film_id
        ORDER BY f.release_year DESC
        LIMIT %s OFFSET %s;
    """
    cursor.execute(query, (year_from, year_to, limit, offset))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        f"🎬 <b>{r['title']}</b> ({r['release_year']})\n"
        f"🕒 {r['length']} мин | 🏷️ {r['rating']}\n"
        f"🎭 Жанры: {r['genres']}\n"
        f"🎤 Актёры: {r['actors']}\n"
        f"📄 {r['description'][:300]}..."
        for r in results
    ]

def search_actors_by_name(name: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT actor_id, first_name, last_name
    FROM actor
    WHERE first_name LIKE %s OR last_name LIKE %s
    LIMIT 10
    """
    cursor.execute(query, (f"%{name}%", f"%{name}%"))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def get_actor_info(actor_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT a.first_name, a.last_name,
           f.title, c.name AS genre, f.release_year, f.rating
    FROM actor a
    JOIN film_actor fa ON a.actor_id = fa.actor_id
    JOIN film f ON fa.film_id = f.film_id
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    WHERE a.actor_id = %s
    """
    cursor.execute(query, (actor_id,))
    results = cursor.fetchall()

    if not results:
        return None

    actor_info = {
        "first_name": results[0]["first_name"],
        "last_name": results[0]["last_name"],
        "films": [
            {
                "title": row["title"],
                "genre": row["genre"],
                "year": row["release_year"],
                "rating": row["rating"]
            }
            for row in results
        ]
    }

    cursor.close()
    conn.close()
    return actor_info


def get_languages():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT language_id, name FROM language ORDER BY name")
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def search_by_language(language_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT f.title, f.release_year, f.rating,
           GROUP_CONCAT(DISTINCT CONCAT(ac.first_name, ' ', ac.last_name) SEPARATOR ', ') AS actors,
           GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genres
    FROM film f
    JOIN film_actor fa ON f.film_id = fa.film_id
    JOIN actor ac ON fa.actor_id = ac.actor_id
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    WHERE f.language_id = %s
    GROUP BY f.film_id
    ORDER BY f.release_year DESC
    """
    cursor.execute(query, (language_id,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        f"<b>{r['title']}</b> ({r['release_year']}, {r['rating']})\n"
        f"🎭 Актёры: {r['actors']}\n"
        f"🎞️ Жанры: {r['genres']}"
        for r in results
    ]


def search_film_availability(title: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT s.store_id, a.address, a.district, c.city, co.country, a.phone, COUNT(i.inventory_id) as count
    FROM inventory i
    JOIN store s ON i.store_id = s.store_id
    JOIN address a ON s.address_id = a.address_id
    JOIN city c ON a.city_id = c.city_id
    JOIN country co ON c.country_id = co.country_id
    JOIN film f ON i.film_id = f.film_id
    WHERE f.title LIKE %s
    GROUP BY s.store_id
    """
    cursor.execute(query, (f"%{title}%",))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def search_film_availability_by_id(film_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT s.store_id, a.address, a.district, c.city, co.country, a.phone, COUNT(i.inventory_id) AS count
    FROM inventory i
    JOIN store s ON i.store_id = s.store_id
    JOIN address a ON s.address_id = a.address_id
    JOIN city c ON a.city_id = c.city_id
    JOIN country co ON c.country_id = co.country_id
    WHERE i.film_id = %s
    GROUP BY s.store_id
    """
    cursor.execute(query, (film_id,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results


def find_films_by_title(title: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT film_id, title
    FROM film
    WHERE title LIKE %s
    ORDER BY title
    LIMIT 10
    """
    cursor.execute(query, (f"%{title}%",))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def get_recent_films():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        f.title, 
        f.release_year, 
        f.rating,
        GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genres,
        GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
    FROM film f
    JOIN film_actor fa ON f.film_id = fa.film_id
    JOIN actor a ON fa.actor_id = a.actor_id
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    GROUP BY f.film_id, f.title, f.release_year, f.rating
    ORDER BY f.last_update DESC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        f"<b>{r['title']}</b> ({r['release_year']}, {r['rating']})\n"
        f"🎭 Актёры: {r['actors']}\n"
        f"🎞️ Жанры: {r['genres']}"
        for r in results
    ]

def get_special_films():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT title, length, rating
    FROM all_about_film
    WHERE length >= 120 OR rating = 'NC-17'
    ORDER BY length DESC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return [f"📽️ {r['title']} — 🕒 {r['length']} мин | {r['rating']}" for r in results]

def get_genre_map():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT category_id, name FROM category")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {row["category_id"]: row["name"] for row in rows}

def get_language_map():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT language_id, name FROM language")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {row["language_id"]: row["name"] for row in rows}
