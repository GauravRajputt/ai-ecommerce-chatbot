import streamlit as st

from faq import ingest_faq_data, faq_chain
from sql import sql_chain
from pathlib import Path
from router import router


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="E-Commerce Bot",
    page_icon="🛍️",
    layout="wide"
)


# ============================================================
# FAQ DATA
# ============================================================

faqs_path = (
    Path(__file__).parent
    / "resources"
    / "faq_data.csv"
)

ingest_faq_data(
    faqs_path
)


# ============================================================
# ROUTER
# ============================================================

def ask(query):

    try:

        route = router(query)

        if route is None:

            return {
                "type": "text",
                "answer": (
                    "Sorry, I couldn't understand "
                    "your request."
                )
            }

        route_name = route.name

        # ----------------------------------------------------
        # FAQ
        # ----------------------------------------------------

        if route_name == "faq":

            return {
                "type": "text",
                "answer": faq_chain(query)
            }

        # ----------------------------------------------------
        # SQL
        # ----------------------------------------------------

        elif route_name == "sql":

            result = sql_chain(
                query
            )

            return {
                "type": "products",
                "answer": result.get(
                    "answer",
                    ""
                ),
                "products": result.get(
                    "products",
                    []
                )
            }

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        else:

            return {
                "type": "text",
                "answer": (
                    f"Route {route_name} "
                    "is not implemented yet."
                )
            }

    except Exception as e:

        print(
            f"Application error: {e}"
        )

        return {
            "type": "text",
            "answer": (
                "⚠️ Something went wrong. "
                "Please try again."
            )
        }


# ============================================================
# PRODUCT CARD
# ============================================================

def display_product(product):

    title = product.get(
        "title",
        "Unknown Product"
    )

    price = product.get(
        "price",
        0
    )

    discount = product.get(
        "discount",
        0
    )

    rating = product.get(
        "rating",
        0
    )

    image_url = product.get(
        "image_url"
    )

    product_link = product.get(
        "product_link"
    )

    # Convert decimal discount to percentage
    discount_percentage = (
        discount * 100
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if image_url:

        try:

            st.image(
                image_url,
                use_container_width=True
            )

        except Exception:

            st.info(
                "Product image unavailable"
            )

    else:

        st.info(
            "Product image unavailable"
        )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    st.markdown(
        f"### {title}"
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    st.markdown(
        f"**₹{price:,.0f}**"
    )

    # --------------------------------------------------------
    # DISCOUNT + RATING
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if discount_percentage > 0:

            st.write(
                f"🏷️ {discount_percentage:.0f}% OFF"
            )

        else:

            st.write(
                "🏷️ No discount"
            )

    with col2:

        st.write(
            f"⭐ {rating:.1f}/5"
        )

    # --------------------------------------------------------
    # VIEW PRODUCT
    # --------------------------------------------------------

    if product_link:

        st.link_button(
            "🛒 View Product",
            product_link,
            use_container_width=True
        )


# ============================================================
# DISPLAY PRODUCT RESULTS
# ============================================================

def display_products(
    products
):

    if not products:

        return

    # --------------------------------------------------------
    # DISPLAY IN 4 COLUMNS
    # --------------------------------------------------------

    columns = st.columns(4)

    for index, product in enumerate(
        products
    ):

        column = columns[
            index % 4
        ]

        with column:

            with st.container(
                border=True
            ):

                display_product(
                    product
                )


# ============================================================
# PAGE TITLE
# ============================================================

st.title(
    "🛍️ E-Commerce Bot"
)

st.caption(
    "Search products, check prices, ratings, "
    "discounts and get product links."
)


# ============================================================
# CHAT HISTORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# DISPLAY PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        # ----------------------------------------------------
        # PRODUCT MESSAGE
        # ----------------------------------------------------

        if message.get(
            "type"
        ) == "products":

            st.markdown(
                message.get(
                    "answer",
                    ""
                )
            )

            display_products(
                message.get(
                    "products",
                    []
                )
            )

        # ----------------------------------------------------
        # NORMAL MESSAGE
        # ----------------------------------------------------

        else:

            st.markdown(
                message.get(
                    "content",
                    ""
                )
            )


# ============================================================
# CHAT INPUT
# ============================================================

query = st.chat_input(
    "Ask about products or store policies..."
)


# ============================================================
# PROCESS QUERY
# ============================================================

if query:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            query
        )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
            "type": "text"
        }
    )

    # --------------------------------------------------------
    # ASSISTANT
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Searching..."
        ):

            result = ask(
                query
            )

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        if result.get(
            "type"
        ) == "products":

            st.markdown(
                result.get(
                    "answer",
                    ""
                )
            )

            display_products(
                result.get(
                    "products",
                    []
                )
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "type": "products",
                    "answer": result.get(
                        "answer",
                        ""
                    ),
                    "products": result.get(
                        "products",
                        []
                    )
                }
            )

        # ----------------------------------------------------
        # NORMAL TEXT
        # ----------------------------------------------------

        else:

            answer = result.get(
                "answer",
                ""
            )

            st.markdown(
                answer
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": answer
                }
            )