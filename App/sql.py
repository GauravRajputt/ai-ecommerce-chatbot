import os
import re
import sqlite3
import time
import requests
import pandas as pd

from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from google import genai
from google.genai import types
from google.genai.errors import ServerError


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not found.\n"
        "Please add GEMINI_API_KEY to your .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# DATABASE PATH
# ============================================================

db_path = Path(__file__).parent / "db.sqlite"

print(f"Using Gemini model: {GEMINI_MODEL}")
print(f"Database path: {db_path}")


# ============================================================
# CREATE IMAGE CACHE TABLE
# ============================================================

def create_image_cache_table():

    try:

        with sqlite3.connect(db_path) as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS product_images (
                    product_link TEXT PRIMARY KEY,
                    image_url TEXT
                )
                """
            )

            conn.commit()

    except Exception as e:

        print(
            f"Could not create image cache table: {e}"
        )


create_image_cache_table()


# ============================================================
# SQL GENERATION PROMPT
# ============================================================

sql_prompt = """
You are an expert SQLite SQL query generator for an e-commerce database.

DATABASE SCHEMA
===============

Table: product

Columns:

product_link
- string
- URL/link to the product

title
- string
- product name

brand
- string
- product brand

price
- integer
- product price in Indian Rupees

discount
- float
- discount stored as decimal
- 0.10 means 10%
- 0.40 means 40%

avg_rating
- float
- average product rating
- range: 0 to 5

total_ratings
- integer
- total number of ratings


IMPORTANT RULES
===============

1. Generate exactly ONE SQLite SELECT query.

2. The table name is:
product

3. Only use these columns:

product_link
title
brand
price
discount
avg_rating
total_ratings

4. Never use columns that do not exist.

5. Never generate:
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
REPLACE
ATTACH
DETACH
PRAGMA

6. The query must always be a SELECT query.

7. Use case-insensitive brand matching:

LOWER(brand) LIKE LOWER('%Nike%')

8. Do not use ILIKE because SQLite does not support ILIKE.


PRICE RULES
===========

"under 3000"
"below 3000"
"less than 3000"

means:

price < 3000


"up to 3000"
"3000 or less"

means:

price <= 3000


"above 3000"
"more than 3000"

means:

price > 3000


"at least 3000"
"3000 or more"

means:

price >= 3000


"between 2000 and 5000"

means:

price BETWEEN 2000 AND 5000


RATING RULES
============

"rating above 4"
"rating more than 4"
"rating greater than 4"

means:

avg_rating > 4


"rating 4 or above"
"rating at least 4"

means:

avg_rating >= 4


"rating below 4"

means:

avg_rating < 4


"rating 4 or below"

means:

avg_rating <= 4


"highest rated"
"best rated"
"top rated"

means:

ORDER BY avg_rating DESC


"lowest rated"

means:

ORDER BY avg_rating ASC


PRICE SORTING
=============

"cheapest"

means:

ORDER BY price ASC


"most expensive"

means:

ORDER BY price DESC


DISCOUNT RULES
==============

Discount is stored as a decimal.

20% = 0.20
30% = 0.30
40% = 0.40
50% = 0.50


"discount above 30%"

means:

discount > 0.30


"discount at least 30%"

means:

discount >= 0.30


"discount below 30%"

means:

discount < 0.30


"discounted products"

means:

discount > 0


COMBINED FILTERS
================

For:

"Show me Nike shoes under 3000"

the query MUST contain:

LOWER(brand) LIKE LOWER('%Nike%')

AND

price < 3000


For:

"Show me Nike shoes rated above 4"

the query MUST contain:

LOWER(brand) LIKE LOWER('%Nike%')

AND

avg_rating > 4


LIMIT
=====

If the user specifies a number of products,
use LIMIT.

OUTPUT FORMAT
=============

Return ONLY the complete SQL query.

Do not provide explanations.

Do not use markdown code blocks.

Do not use <SQL> tags.

The SQL query must be complete and valid SQLite.
"""


# ============================================================
# NORMALIZE GEMINI SQL
# ============================================================

def normalize_gemini_sql(response_text):

    if not response_text:
        return None

    sql = response_text.strip()

    sql = re.sub(
        r"</?SQL>",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"```",
        "",
        sql
    )

    sql = sql.strip()

    match = re.search(
        r"\bSELECT\b",
        sql,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    sql = sql[match.start():].strip()

    sql = sql.rstrip(";").strip()

    return sql


# ============================================================
# CHECK SQL COMPLETENESS
# ============================================================

def is_complete_sql(sql):

    if not sql:
        return False

    sql_upper = sql.upper().strip()

    if not sql_upper.startswith("SELECT"):
        return False

    if not re.search(
        r"\bFROM\b",
        sql_upper
    ):
        return False

    if not re.search(
        r"\bFROM\s+product\b",
        sql_upper
    ):
        return False

    if sql.count("(") != sql.count(")"):
        return False

    if sql.count("'") % 2 != 0:
        return False

    if sql.count('"') % 2 != 0:
        return False

    incomplete_endings = [
        "WHERE",
        "AND",
        "OR",
        "LIKE",
        "LOWER(",
        "ORDER BY",
        "GROUP BY",
        "LIMIT",
        "=",
        ">",
        "<",
        ">=",
        "<="
    ]

    for ending in incomplete_endings:

        if sql_upper.endswith(ending):
            return False

    return True


# ============================================================
# GENERATE SQL USING GEMINI
# ============================================================

def generate_sql_query(question):

    for attempt in range(3):

        try:

            print(
                f"\nSending SQL generation request to Gemini "
                f"(attempt {attempt + 1}/3)..."
            )

            response = gemini_client.models.generate_content(

                model=GEMINI_MODEL,

                contents=(
                    sql_prompt
                    + "\n\nUSER QUESTION:\n"
                    + question
                ),

                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=1000
                )
            )

            print("Gemini response received.")

            content = response.text

            if not content:

                print(
                    "Gemini returned an empty response."
                )

                continue

            sql = normalize_gemini_sql(
                content
            )

            if sql is None:

                print(
                    "Gemini response did not contain SQL."
                )

                continue

            if not is_complete_sql(sql):

                print(
                    "Gemini returned incomplete SQL."
                )

                continue

            return sql

        except ServerError as e:

            print(
                f"Gemini SQL generation failed "
                f"(attempt {attempt + 1}/3): {e}"
            )

            if attempt < 2:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        except Exception as e:

            print(
                f"Gemini SQL generation failed: {e}"
            )

            break

    return None


# ============================================================
# FALLBACK SQL GENERATOR
# ============================================================

def fallback_sql_query(question):

    q = question.lower().strip()

    conditions = []
    order_by = None
    limit = None

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    known_brands = [
        "nike",
        "adidas",
        "puma",
        "reebok",
        "sparx",
        "bata",
        "skechers",
        "woodland",
        "campus",
        "asian",
        "red tape"
    ]

    brand = None

    for possible_brand in known_brands:

        if possible_brand in q:

            brand = possible_brand
            break

    if brand:

        conditions.append(
            f"LOWER(brand) LIKE LOWER('%{brand}%')"
        )

    # --------------------------------------------------------
    # PRICE BETWEEN
    # --------------------------------------------------------

    between_match = re.search(
        r"(?:between|from)\s*₹?\s*(\d+)"
        r"\s*(?:and|to|-)\s*₹?\s*(\d+)",
        q
    )

    if between_match:

        low = int(
            between_match.group(1)
        )

        high = int(
            between_match.group(2)
        )

        if low > high:
            low, high = high, low

        conditions.append(
            f"price BETWEEN {low} AND {high}"
        )

    else:

        # ----------------------------------------------------
        # UNDER / BELOW / LESS THAN
        # ----------------------------------------------------

        price_match = re.search(
            r"(?:under|below|less than)\s*₹?\s*(\d+)",
            q
        )

        if price_match:

            price = int(
                price_match.group(1)
            )

            conditions.append(
                f"price < {price}"
            )

        # ----------------------------------------------------
        # UP TO
        # ----------------------------------------------------

        else:

            price_match = re.search(
                r"(?:up to|upto)\s*₹?\s*(\d+)",
                q
            )

            if price_match:

                price = int(
                    price_match.group(1)
                )

                conditions.append(
                    f"price <= {price}"
                )

        # ----------------------------------------------------
        # ABOVE / MORE THAN
        # ----------------------------------------------------

        price_match = re.search(
            r"(?:above|more than|greater than)\s*₹?\s*(\d+)",
            q
        )

        if price_match:

            price = int(
                price_match.group(1)
            )

            conditions.append(
                f"price > {price}"
            )

        # ----------------------------------------------------
        # AT LEAST
        # ----------------------------------------------------

        price_match = re.search(
            r"(?:at least)\s*₹?\s*(\d+)",
            q
        )

        if price_match:

            price = int(
                price_match.group(1)
            )

            conditions.append(
                f"price >= {price}"
            )

    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    rating_match = re.search(
        r"(?:rating|rated)\s*"
        r"(?:above|over|greater than|more than)\s*"
        r"(\d+(?:\.\d+)?)",
        q
    )

    if rating_match:

        rating = float(
            rating_match.group(1)
        )

        conditions.append(
            f"avg_rating > {rating}"
        )

    else:

        rating_match = re.search(
            r"(?:rating|rated)\s*"
            r"(?:at least|or above)\s*"
            r"(\d+(?:\.\d+)?)",
            q
        )

        if rating_match:

            rating = float(
                rating_match.group(1)
            )

            conditions.append(
                f"avg_rating >= {rating}"
            )

    # --------------------------------------------------------
    # HIGHEST RATED
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "highest rated",
            "highest rating",
            "best rated",
            "top rated",
            "best products"
        ]
    ):

        order_by = "avg_rating DESC"

    # --------------------------------------------------------
    # CHEAPEST
    # --------------------------------------------------------

    if "cheapest" in q:

        order_by = "price ASC"

    # --------------------------------------------------------
    # MOST EXPENSIVE
    # --------------------------------------------------------

    if (
        "most expensive" in q
        or "highest price" in q
    ):

        order_by = "price DESC"

    # --------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------

    discount_match = re.search(
        r"discount\s*"
        r"(?:above|over|more than|greater than)\s*"
        r"(\d+(?:\.\d+)?)\s*%",
        q
    )

    if discount_match:

        discount = float(
            discount_match.group(1)
        ) / 100

        conditions.append(
            f"discount > {discount}"
        )

    # --------------------------------------------------------
    # DISCOUNTED PRODUCTS
    # --------------------------------------------------------

    if (
        "discounted" in q
        or "on sale" in q
    ):

        conditions.append(
            "discount > 0"
        )

    # --------------------------------------------------------
    # LIMIT
    # --------------------------------------------------------

    limit_match = re.search(
        r"\b(\d+)\s+(?:products?|shoes?|items?)\b",
        q
    )

    if limit_match:

        limit = int(
            limit_match.group(1)
        )

    # --------------------------------------------------------
    # BUILD SQL
    # --------------------------------------------------------

    sql = "SELECT * FROM product"

    if conditions:

        sql += "\nWHERE " + "\nAND ".join(
            conditions
        )

    if order_by:

        sql += f"\nORDER BY {order_by}"

    if limit:

        sql += f"\nLIMIT {limit}"

    if not conditions and not order_by and not limit:

        return None

    return sql


# ============================================================
# CLEAN SQL
# ============================================================

def clean_sql(sql_query):

    if not sql_query:
        return None

    sql_query = sql_query.strip()

    sql_query = re.sub(
        r"</?SQL>",
        "",
        sql_query,
        flags=re.IGNORECASE
    )

    sql_query = re.sub(
        r"^```sql\s*",
        "",
        sql_query,
        flags=re.IGNORECASE
    )

    sql_query = re.sub(
        r"^```\s*",
        "",
        sql_query
    )

    sql_query = re.sub(
        r"\s*```$",
        "",
        sql_query
    )

    sql_query = sql_query.rstrip(";").strip()

    return sql_query


# ============================================================
# VALIDATE SQL
# ============================================================

def validate_sql(query):

    if not query:
        return False

    query = query.strip()

    if not query.upper().startswith("SELECT"):

        print(
            "Blocked query: Not a SELECT query."
        )

        return False

    if not re.search(
        r"\bFROM\s+product\b",
        query,
        flags=re.IGNORECASE
    ):

        print(
            "Blocked query: Invalid table."
        )

        return False

    forbidden_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "PRAGMA"
    ]

    upper_query = query.upper()

    for keyword in forbidden_keywords:

        if re.search(
            rf"\b{keyword}\b",
            upper_query
        ):

            print(
                f"Blocked dangerous SQL keyword: {keyword}"
            )

            return False

    if ";" in query:

        print(
            "Blocked query: Multiple SQL statements detected."
        )

        return False

    return True


# ============================================================
# RUN SQL QUERY
# ============================================================

def run_query(query):

    if not validate_sql(query):
        return None

    try:

        with sqlite3.connect(db_path) as conn:

            df = pd.read_sql_query(
                query,
                conn
            )

        return df

    except Exception as e:

        print(
            f"Database error: {e}"
        )

        return None


# ============================================================
# IMAGE EXTRACTION
# ============================================================

def get_cached_image(product_link):

    try:

        with sqlite3.connect(db_path) as conn:

            row = conn.execute(
                """
                SELECT image_url
                FROM product_images
                WHERE product_link = ?
                """,
                (product_link,)
            ).fetchone()

        if row and row[0]:

            return row[0]

    except Exception as e:

        print(
            f"Image cache read error: {e}"
        )

    return None


def save_cached_image(
    product_link,
    image_url
):

    try:

        with sqlite3.connect(db_path) as conn:

            conn.execute(
                """
                INSERT OR REPLACE INTO product_images
                (product_link, image_url)
                VALUES (?, ?)
                """,
                (
                    product_link,
                    image_url
                )
            )

            conn.commit()

    except Exception as e:

        print(
            f"Image cache save error: {e}"
        )


@lru_cache(maxsize=100)
def get_product_image(product_link):

    if not product_link:
        return None

    product_link = str(
        product_link
    ).strip()

    if not product_link:
        return None

    # --------------------------------------------------------
    # CHECK DATABASE CACHE
    # --------------------------------------------------------

    cached_image = get_cached_image(
        product_link
    )

    if cached_image:

        return cached_image

    # --------------------------------------------------------
    # REQUEST PRODUCT PAGE
    # --------------------------------------------------------

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }

        response = requests.get(
            product_link,
            headers=headers,
            timeout=8
        )

        if response.status_code != 200:

            print(
                f"Product page returned "
                f"{response.status_code}"
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # ----------------------------------------------------
        # METHOD 1: OPEN GRAPH
        # ----------------------------------------------------

        image_tag = soup.find(
            "meta",
            property="og:image"
        )

        if image_tag:

            image_url = image_tag.get(
                "content"
            )

            if image_url:

                save_cached_image(
                    product_link,
                    image_url
                )

                return image_url

        # ----------------------------------------------------
        # METHOD 2: TWITTER IMAGE
        # ----------------------------------------------------

        image_tag = soup.find(
            "meta",
            attrs={
                "name": "twitter:image"
            }
        )

        if image_tag:

            image_url = image_tag.get(
                "content"
            )

            if image_url:

                save_cached_image(
                    product_link,
                    image_url
                )

                return image_url

        # ----------------------------------------------------
        # METHOD 3: JSON-LD
        # ----------------------------------------------------

        json_ld_tags = soup.find_all(
            "script",
            type="application/ld+json"
        )

        for tag in json_ld_tags:

            try:

                import json

                data = json.loads(
                    tag.string or tag.text
                )

                objects = []

                if isinstance(data, list):
                    objects = data

                elif isinstance(data, dict):

                    objects = [data]

                    if "@graph" in data:

                        objects.extend(
                            data["@graph"]
                        )

                for obj in objects:

                    if not isinstance(
                        obj,
                        dict
                    ):
                        continue

                    image = obj.get(
                        "image"
                    )

                    if isinstance(
                        image,
                        str
                    ):

                        save_cached_image(
                            product_link,
                            image
                        )

                        return image

                    if isinstance(
                        image,
                        list
                    ) and image:

                        image = image[0]

                        if isinstance(
                            image,
                            str
                        ):

                            save_cached_image(
                                product_link,
                                image
                            )

                            return image

            except Exception:
                continue

    except requests.RequestException as e:

        print(
            f"Could not fetch product image: {e}"
        )

    except Exception as e:

        print(
            f"Image extraction error: {e}"
        )

    return None


# ============================================================
# FORMAT PRICE
# ============================================================

def format_price(price):

    try:

        price = float(price)

        return f"₹{price:,.0f}"

    except Exception:

        return "₹N/A"


# ============================================================
# FORMAT DISCOUNT
# ============================================================

def format_discount(discount):

    try:

        discount = float(discount)

        percentage = discount * 100

        return f"{percentage:.0f}%"

    except Exception:

        return "0%"


# ============================================================
# FORMAT RATING
# ============================================================

def format_rating(rating):

    try:

        return f"{float(rating):.1f}"

    except Exception:

        return "N/A"


# ============================================================
# FORMAT PRODUCT DATA
# ============================================================

def prepare_products(df):

    if df is None or df.empty:

        return []

    products = []

    # Show maximum 8 products in UI
    display_df = df.head(8)

    for _, row in display_df.iterrows():

        title = str(
            row.get(
                "title",
                "Unknown Product"
            )
        )

        price = row.get(
            "price",
            0
        )

        discount = row.get(
            "discount",
            0
        )

        rating = row.get(
            "avg_rating",
            0
        )

        product_link = str(
            row.get(
                "product_link",
                ""
            )
        ).strip()

        image_url = get_product_image(
            product_link
        )

        products.append(
            {
                "title": title,
                "price": float(price)
                if pd.notna(price)
                else 0,

                "discount": float(discount)
                if pd.notna(discount)
                else 0,

                "rating": float(rating)
                if pd.notna(rating)
                else 0,

                "product_link": product_link,

                "image_url": image_url
            }
        )

    return products


# ============================================================
# SQL CHAIN
# ============================================================

def sql_chain(question):

    # --------------------------------------------------------
    # TRY GEMINI
    # --------------------------------------------------------

    sql_query = generate_sql_query(
        question
    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if sql_query is None:

        print(
            "\nGemini failed or returned incomplete SQL."
        )

        print(
            "Trying deterministic Python SQL fallback..."
        )

        sql_query = fallback_sql_query(
            question
        )

        if sql_query is None:

            return {
                "answer": (
                    "⚠️ I couldn't generate a valid "
                    "product query for your request."
                ),
                "products": []
            }

        print(
            "\nFallback SQL generated."
        )

    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    sql_query = clean_sql(
        sql_query
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    if not validate_sql(
        sql_query
    ):

        print(
            "Generated SQL failed validation."
        )

        sql_query = fallback_sql_query(
            question
        )

        if sql_query is None:

            return {
                "answer": (
                    "⚠️ Sorry, I couldn't generate "
                    "a safe SQL query."
                ),
                "products": []
            }

    # --------------------------------------------------------
    # PRINT SQL
    # --------------------------------------------------------

    print(
        "\n=============================="
    )

    print(
        "FINAL SQL QUERY"
    )

    print(
        "=============================="
    )

    print(
        sql_query
    )

    # --------------------------------------------------------
    # RUN QUERY
    # --------------------------------------------------------

    response = run_query(
        sql_query
    )

    if response is None:

        return {
            "answer": (
                "⚠️ Sorry, there was a problem "
                "executing the database query."
            ),
            "products": []
        }

    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if response.empty:

        return {
            "answer": (
                "### No products found\n\n"
                "I couldn't find any products "
                "matching your request."
            ),
            "products": []
        }

    # --------------------------------------------------------
    # PREPARE PRODUCTS
    # --------------------------------------------------------

    products = prepare_products(
        response
    )

    count = len(response)

    if count == 1:

        summary = (
            "I found **1 product** "
            "matching your request."
        )

    else:

        summary = (
            f"I found **{count} products** "
            "matching your request."
        )

    # --------------------------------------------------------
    # RETURN STRUCTURED RESULT
    # --------------------------------------------------------

    return {
        "answer": summary,
        "products": products
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    question = (
        "Show me Nike shoes under 3000"
    )

    result = sql_chain(
        question
    )

    print(
        "\n=============================="
    )

    print(
        "FINAL ANSWER"
    )

    print(
        "=============================="
    )

    print(
        result["answer"]
    )

    print(
        f"\nProducts returned: "
        f"{len(result['products'])}"
    )

    for product in result["products"]:

        print(
            "\nTitle:",
            product["title"]
        )

        print(
            "Image:",
            product["image_url"]
        )

        print(
            "Price:",
            product["price"]
        )

        print(
            "Rating:",
            product["rating"]
        )