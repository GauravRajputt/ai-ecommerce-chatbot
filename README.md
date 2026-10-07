# 🛍️ AI-Powered E-Commerce Chatbot

An AI-powered e-commerce chatbot that allows users to search for products and ask store-related questions using natural language.

For example:

```text
Find highly rated Nike shoes under ₹3,000
```

The chatbot understands the user's request, generates SQL using Gemini for product searches, retrieves matching products from a SQLite database, and provides answers to common store-related questions such as refunds, payments, and order cancellation.

---

## 🚀 Key Features

- 🔎 Natural language product search
- 🤖 Gemini-powered SQL generation
- 🗄️ SQLite product database
- 🖼️ Product images
- 🔗 Direct product links
- ⭐ Price, discount and rating filters
- 💳 Payment-related queries
- 🔄 Refund and return policy queries
- ❌ Order cancellation queries
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
```

For store-related questions:

```text
User Question
    ↓
Query Processing
    ↓
Store Information
    ↓
AI Response
```

---

## 🧠 How It Works

### Product Search

1. User enters a natural-language product query.
2. Gemini understands the required filters.
3. Gemini generates an SQL query.
4. The SQL query is validated.
5. The query is executed on the SQLite database.
6. Matching products are displayed with price, rating, discount, images and product links.

Example:

```text
Find Nike running shoes under ₹3,000 with a rating above 4
```

Example SQL:

```sql
SELECT *
FROM product
WHERE LOWER(brand) LIKE LOWER('%nike%')
AND LOWER(title) LIKE LOWER('%shoe%')
AND price < 3000
AND avg_rating > 4;
```

### Store Support

The chatbot can also answer questions such as:

```text
What is your refund policy?
```

```text
Do you accept UPI payments?
```

```text
Can I cancel my order?
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

### 🔎 Product Search

```text
Find Nike running shoes under ₹3,000 with a rating above 4
```

```text
Show me Adidas products below ₹5,000
```

### 💳 Payment

```text
Do you accept UPI payments?
```

### 🔄 Refund

```text
What is your refund policy?
```

```text
How long does it take to get a refund?
```

### ❌ Cancellation

```text
Can I cancel my order?
```

---

## 📸 Screenshots

### Product Search

![AI E-Commerce Product Search](screenshots/product-search.png)

### Refund & Payment

![Refund and Payment Support](screenshots/refund-payment.png)

### Order Cancellation

![Order Cancellation Support](screenshots/order-cancellation.png)

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
🔎 Natural Language Product Search
🧠 AI-Based SQL Generation
🗄️ SQLite Database
💳 Payment Support
🔄 Refund & Return Support
❌ Order Cancellation
🖼️ Product Images
🎨 Streamlit
🐍 Python
```
