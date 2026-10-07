# 🛍️ AI-Powered E-Commerce Chatbot

An AI-powered e-commerce chatbot that allows users to search for products using natural language instead of manually applying multiple filters.

For example:

```text
Show me Nike shoes under 3000 with rating above 4
```

The application understands the query, generates a SQL query using Gemini, searches the SQLite product database, and displays relevant products with details, images, ratings, prices, and direct product links.

---

## 🚀 Key Features

- 🔎 Natural language product search
- 🤖 Gemini-powered SQL generation
- 🗄️ SQLite product database
- 🖼️ Product image support
- 🔗 Direct product links
- 🛡️ SQL validation
- 🔄 AI fallback mechanism
- 🎨 Interactive Streamlit interface

---

## 🏗️ System Architecture

```text
User Query
    ↓
Streamlit Interface
    ↓
Query Processing
    ↓
Gemini AI
    ↓
SQL Generation & Validation
    ↓
SQLite Database
    ↓
Product Results
    ↓
Images + Price + Rating + Product Link
```

---

## 🧠 How It Works

1. User enters a natural-language product query.
2. The application identifies the required filters.
3. Gemini converts the request into SQL.
4. The generated SQL is validated.
5. The query is executed on the SQLite database.
6. Matching products are retrieved.
7. Products are displayed through the Streamlit interface.

Example:

```text
User:
Show me Nike shoes under 3000 with rating above 4
```

The system generates a query similar to:

```sql
SELECT *
FROM product
WHERE LOWER(brand) LIKE LOWER('%nike%')
AND LOWER(title) LIKE LOWER('%shoe%')
AND price < 3000
AND avg_rating > 4;
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Streamlit | Web interface |
| Gemini | AI & SQL generation |
| SQLite | Product database |
| Pandas | Data processing |
| SQL | Database querying |
| Requests | Web requests |
| BeautifulSoup | HTML parsing |
| Semantic Router | Query routing |

---

## 📂 Project Structure

```text
E-com-tool/
│
├── App/
│   ├── main.py
│   ├── sql.py
│   ├── router.py
│   ├── db.sqlite
│   └── resources/
│
├── db.sqlite
├── requirements.txt
├── .gitignore
└── README.md
```

---


## ▶️ Run the Application

```bash
streamlit run App/main.py
```

---

## 💬 Example Queries

```text
Show me Nike shoes under 3000
```

```text
Find products with rating above 4
```

```text
Show me Adidas products below 5000
```

```text
Find Nike products below 3000 with rating above 4
```

---

## 🎥 Demo

Add your project demo video here after uploading it to GitHub.

```text
https://github.com/user-attachments/assets/your-video-id
```

---

## 👨‍💻 Author

### Gaurav Rajputt

B.Tech – Artificial Intelligence & Data Science  
Thakur College of Engineering & Technology, Mumbai

**GitHub:**  
https://github.com/GauravRajputt

---

## ⭐ Project Highlights

```text
🤖 Generative AI
🔎 Natural Language Search
🧠 AI-Based SQL Generation
🗄️ SQLite Database
🖼️ Product Images
🔗 Product Links
🎨 Streamlit
🐍 Python
```

```
