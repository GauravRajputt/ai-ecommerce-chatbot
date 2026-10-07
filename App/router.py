from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder


# ============================================================
# ENCODER
# ============================================================

encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# FAQ ROUTE
# ============================================================

faq = Route(
    name="faq",

    utterances=[
        # Return / Refund
        "What is the return policy?",
        "What is your return policy?",
        "Can I return a product?",
        "How do I return my order?",
        "Can I get a refund?",
        "How long does a refund take?",
        "What is the refund policy?",
        "How long does it take to process a refund?",

        # Order tracking
        "How can I track my order?",
        "Where is my order?",
        "How do I track my order?",
        "Can I track my package?",
        "Where can I see my order status?",

        # Payment
        "What payment methods are accepted?",
        "How can I pay for my order?",
        "Do you accept credit cards?",
        "Do you accept debit cards?",
        "Can I pay using UPI?",

        # Discounts / offers
        "Do I get discount with HDFC credit card?",
        "Is there a discount on HDFC credit cards?",
        "What credit card offers are available?",
        "Are there any payment offers?",
    ]
)


# ============================================================
# SQL ROUTE
# ============================================================

sql = Route(
    name="sql",

    utterances=[
        # ----------------------------------------------------
        # BRAND SEARCH
        # ----------------------------------------------------

        "Show me Nike shoes",
        "Show me Nike products",
        "I want Nike shoes",
        "Find Nike shoes",
        "Do you have Nike shoes?",
        "What Nike shoes do you have?",
        "Show Nike running shoes",
        "Show me Puma shoes",
        "Show me Adidas shoes",
        "Show me Reebok shoes",
        "Are there any Puma shoes on sale?",
        "What is the price of Puma running shoes?",

        # ----------------------------------------------------
        # RATING
        # ----------------------------------------------------

        "Show me shoes with rating more than 4",
        "Show me shoes rated above 4",
        "Show products with rating above 4",
        "Show products with rating more than 4",
        "Find shoes with rating greater than 4",
        "Which shoes have a rating above 4?",
        "Show Nike shoes with rating more than 4",
        "Show Nike shoes rated above 4",
        "Show Nike products with rating above 4",
        "Find Nike shoes with rating greater than 4",
        "Show me the Nike shoes that have rating more than 4",

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        "Show me shoes under Rs. 3000",
        "Are there any shoes under Rs. 3000?",
        "Find shoes below 3000",
        "Show products below Rs. 3000",
        "Which shoes cost less than 3000?",
        "Show me shoes between Rs. 2000 and Rs. 5000",
        "Find shoes in the price range 2000 to 5000",
        "Show products between 3000 and 5000",

        # ----------------------------------------------------
        # DISCOUNT
        # ----------------------------------------------------

        "Show me shoes with 50% discount",
        "Find shoes with more than 30% discount",
        "Show products with discount above 20%",
        "Which shoes have the highest discount?",
        "Show Nike shoes with 40% discount",
        "Show discounted Nike shoes",
        "Find Nike shoes on sale",

        # ----------------------------------------------------
        # PRODUCT TYPE
        # ----------------------------------------------------

        "Show me running shoes",
        "Show me formal shoes",
        "Show me training shoes",
        "Show me sports shoes",
        "Find running shoes",
        "Find formal shoes",

        # ----------------------------------------------------
        # SIZE
        # ----------------------------------------------------

        "Do you have formal shoes in size 9?",
        "Show me shoes in size 9",
        "Find shoes available in size 9",

        # ----------------------------------------------------
        # GENERAL PRODUCT QUESTIONS
        # ----------------------------------------------------

        "What is the price of Nike shoes?",
        "How much do Nike shoes cost?",
        "Which Nike shoes are available?",
        "What are the cheapest Nike shoes?",
        "What are the most expensive Nike shoes?",
        "Show me the top rated shoes",
        "Which shoes have the highest rating?",
        "Show me the best rated products",
    ]
)


# ============================================================
# CREATE ROUTER
# ============================================================

router = SemanticRouter(
    routes=[faq, sql],
    encoder=encoder
)


# ============================================================
# BUILD INDEX
# ============================================================

router.sync(sync_mode="local")


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_queries = [
        "What is your policy on defective product?",
        "Pink Puma shoes in price range 5000 to 1000",
        "Show me Nike shoes that have rating more than 4",
        "Are there any shoes under 3000?",
        "How can I track my order?",
        "What payment methods are accepted?",
    ]

    for query in test_queries:

        result = router(query)

        print("\nQuery:", query)

        if result is None:
            print("Route: None")

        else:
            print("Route:", result.name)