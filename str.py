import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from datetime import date


import mysql.connector 
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678", 
    database = "brickview"
    
)

print("Connected successfully!")

cur = conn.cursor()
st.sidebar.title("OPTIONS")

page = st.sidebar.radio("Navigate", ["intro", "Filters & Explorer","visualizations", "crud", "SQL_questions"]) 

if page == "intro":
    st.image(r"C:\Users\user\Desktop\ChatGPT Image Apr 26, 2026, 09_34_31 PM.png", 
             caption="Brick View Real Estate Project",
             use_container_width=True)   

    

# if page == "filters":
#     option = st.radio("select the option: "
#                       ["listings", "city", "property type", "sold", "available"],
#                       horizontal=True)    
#     if option == "listings":
#         query = " select * from listings "
#         opt1 = pd.read_sql(query, conn) 
#         st.write(opt1)
#     elif option == "city":
#         query = " select city, avg(price) as avg_price from listings GROUP BY city"
#         opt2 = pd.read_sql(query, conn) 
#         st.write(opt2)
#     elif option == "property type":
#         query = " select  property_type, avg(price) as avg_price from listings GROUP BY property_type"
#         opt3 = pd.read_sql(query, conn) 
#         st.write(opt3)
#     elif option == "sold":
#         query = " select  listing_id, sale_price as price from sales"
#         opt4 = pd.read_sql(query, conn) 
#         st.write(opt4) 
#     elif option == "available":
#         query = " SELECT l.listing_id, l.price FROM listings l LEFT JOIN sales s ON l.listing_id = s.listing_id WHERE s.date_sold IS NULL"
#         opt5 = pd.read_sql(query, conn) 
#         st.write(opt5)

elif page == "Filters & Explorer":
    st.markdown("<p class='section-header'>Filters & Property Explorer</p>", unsafe_allow_html=True)

    # Load reference data
    cities        = pd.read_sql("SELECT DISTINCT city FROM listings ORDER BY city", conn)["city"].tolist()
    prop_types    = pd.read_sql("SELECT DISTINCT property_Type FROM listings ORDER BY property_type", conn)["property_Type"].tolist()
    agents_df     = pd.read_sql("SELECT agent_id, name FROM agents ORDER BY name", conn)

    with st.expander("Filter Options", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            sel_cities = st.multiselect("City", cities, default=cities[:3])
            sel_types  = st.multiselect(" Property Type", prop_types, default=prop_types)

        with col2:
            price_min_val = int(pd.read_sql("SELECT MIN(price) FROM listings", conn).iloc[0,0])
            price_max_val = int(pd.read_sql("SELECT MAX(price) FROM listings", conn).iloc[0,0])
            price_range = st.slider(
                "Price Range ($)",
                min_value=price_min_val,
                max_value=price_max_val,
                value=(price_min_val, price_max_val),
                step=10000,
                format="$%d",
            )

        with col3:
            agent_options = ["All"] + agents_df["name"].tolist()
            sel_agent = st.selectbox("Agent", agent_options)

            date_col, date_col2 = st.columns(2)
            with date_col:
                start_date = st.date_input(" Listed From", value=date(2023, 1, 1))
            with date_col2:
                end_date = st.date_input("Listed To", value=date(2024, 12, 31))

    # Build query
    params = []
    query = """
        SELECT l.listing_id, l.city, l.property_type, l.price, l.sqft, l.date_listed, a.name AS Agent,
               p.bedrooms, p.bathrooms, p.year_built, p.furnishing_status, p.parking_available
        FROM listings l
        LEFT JOIN agents a ON l.agent_id = a.agent_id
        LEFT JOIN property p ON l.listing_id = p.listing_id
        WHERE 1=1
    """ 
    # st.write("Query:", query)
    # st.write("Params:", params)
    # st.write("Number of params:", len(params))
    # st.write("Number of placeholders:", query.count("%s"))

    if sel_cities:
        query += f" AND l.city IN ({','.join(['%s']*len(sel_cities))})"
        params.extend(sel_cities)

    if sel_types:
        query += f" AND l.property_type IN ({','.join(['%s']*len(sel_types))})"
        params.extend(sel_types)

    query += " AND l.price BETWEEN %s AND %s"
    params.extend([price_range[0], price_range[1]])

    if sel_agent != "All":
        query += " AND a.name = %s"
        params.append(sel_agent)

    query += " AND l.date_listed BETWEEN %s AND %s"
    params.extend([start_date, end_date])
    query += " LIMIT 5000"

    result_df = pd.read_sql(query, conn, params=params)

    # Summary row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🔍 Results Found", f"{len(result_df):,}")
    if len(result_df):
        m2.metric("💵 Avg Price",    f"${result_df['price'].mean():,.0f}")
        m3.metric("📐 Avg Sqft",     f"{result_df['sqft'].mean():,.0f}")
        m4.metric("Avg Bedrooms", f"{result_df['bedrooms'].mean():.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

    
    st.markdown(f"<b style='color:#e94560;'> Filtered Listings</b>", unsafe_allow_html=True)
    page_size = st.selectbox("Rows per page", [25, 50, 100], index=0)
    total_pages = max(1, (len(result_df) - 1) // page_size + 1)
    page_num = st.number_input("page", min_value=1, max_value=total_pages, value=1, step=1)

    start = (page_num - 1) * page_size
    end   = start + page_size
    display_df = result_df.iloc[start:end].copy()
    display_df["price"] = display_df["price"].apply(lambda x: f"${x:,.0f}")
    display_df["sqft"]  = display_df["sqft"].apply(lambda x: f"{x:,.0f}")
    display_df["parking_available"] = display_df["parking_available"].map({1: "✅", 0: "❌"})

    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing rows {start+1}–{min(end, len(result_df))} of {len(result_df):,}")
   


if page == "visualizations":
     option = st.radio("select the option: ", 
                      ["Avg_price__by_city", "property_type", "furnished_price", "available"],
                      horizontal=True)
     if option == "Avg_price__by_city":
        query = "SELECT city, ROUND(AVG(price), 2) AS avg_price FROM listings GROUP BY city"
        vs1 = pd.read_sql(query, conn) 
        st.bar_chart(vs1, x= "city", y= "avg_price") 
     elif option == "property_type":
        query = " select  property_type, avg(price) as avg_price from listings GROUP BY property_type;"
        vs2 = pd.read_sql(query, conn) 
        st.bar_chart(vs2, x= "property_type", y= "avg_price")
     elif option == "furnished_price":
        query = """
        select p.furnishing_status, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1
        """
        vs3 = pd.read_sql(query, conn) 
        st.bar_chart(vs3, x= "furnishing_status", y= "avg_price")
     elif option == "available":
        query = """
        SELECT l.listing_id, l.price
        FROM listings l LEFT JOIN sales s 
        ON l.listing_id = s.listing_id 
        WHERE s.date_sold IS NULL 
        ORDER BY l.price 
        LIMIT 25
        """
        vs4 = pd.read_sql(query, conn) 
        st.line_chart(vs4, x= "listing_id", y= "price")




if page == "SQL_questions":
    question = st.selectbox(
        "Choose a question:",
        ["1.  What is the average listing price by city?",
         "2.  What is the average price per square foot by property type?",
         "3.  How does furnishing status impact property prices?",
         "4.  Do properties closer to metro stations command higher prices?",
         "5.  Are rented properties priced differently from non-rented ones?",
         "6.  How do bedrooms and bathrooms affect pricing?",
         "7.  Do properties with parking and power backup sell at higher prices?",
         "8.  How does year built influence listing price?",
         "9.  Which cities have the highest average property prices?", 
         "10. How are properties distributed across price buckets?",
         "11. What is the average days on market by city?",
         "12. Which property types sell the fastest?", 
         "13. What percentage of properties are sold above listing price?",
         "14. What is the sale-to-list price ratio by city?", 
         "15. Which listings took more than 90 days to sell?", 
         "16. How does metro distance affect time on market?", 
         "17. What is the monthly sales trend?", 
         "18. Which properties are currently unsold? "
         "19. Which agents have closed the most sales?", 
         "20. Who are the top agents by total sales revenue?", 
         "21. Which agents close deals fastest?",
         "22. Does experience correlate with deals closed?",
         "23. Do agents with higher ratings close deals faster?",
         "24. What is the average commission earned by each agent?",
         "25. Which agents currently have the most active listings?", 
         "26. What percentage of buyers are investors vs end users?",
         "27. Which cities have the highest loan uptake rate?", 
         "28. What is the average loan amount by buyer type?", 
         "29. Which payment mode is most commonly used?",
         "30. Do loan-backed purchases take longer to close?",
         
        ]

         
    )

    if question == "1.  What is the average listing price by city?":
        query1 = """
        SELECT city, ROUND(AVG(price), 2) AS avg_price
        FROM listings
        GROUP BY city
        """
        df1 = pd.read_sql(query1, conn) 
        st.write(df1) 
         
    elif question == "2.  What is the average price per square foot by property type?":
        query2 = """
        SELECT property_type, AVG(price/sqft) AS avg_price_per_sqft 
        FROM listings GROUP BY property_type
        """ 
        df2 = pd.read_sql(query2, conn) 
        st.write(df2) 
    elif question == "3.  How does furnishing status impact property prices?":
        query = """
        select p.furnishing_status, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1
        """
        df3 = pd.read_sql(query, conn) 
        st.write(df3)
    elif question == "4.  Do properties closer to metro stations command higher prices?":
        query = """
        select p.metro_distance_km, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1
        ORDER BY 2 DESC
        """
        df4 = pd.read_sql(query, conn) 
        st.write(df4)
    elif question == "5.  Are rented properties priced differently from non-rented ones?":
        query = """
        select p.is_rented, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1
        ORDER BY 2 DESC
        """
        df5 = pd.read_sql(query, conn) 
        st.write(df5)
    elif question == "6.  How do bedrooms and bathrooms affect pricing?":
        query = """
        select bedrooms, bathrooms, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1,2
        Order by 3
        """ 
        df6 = pd.read_sql(query, conn) 
        st.write(df6)
    elif question == "7.  Do properties with parking and power backup sell at higher prices?":
        query = """
        select parking_available, power_backup, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1,2
        Order by 3;
        """  
        df7 = pd.read_sql(query, conn) 
        st.write(df7) 
    elif question == "8.  How does year built influence listing price?":
        query = """
        select p.year_built, (ROUND(AVG(l.price),2)) as avg_price
        from listings l join property p ON l.listing_id = p.listing_id  
        GROUP BY 1
        ORDER BY 2 DESC;
        """ 
        df8 = pd.read_sql(query, conn) 
        st.write(df8)
    elif question == "9.  Which cities have the highest average property prices?":
        query = """
        SELECT city, ROUND(AVG(price),2) AS avg_price FROM listings
        GROUP BY CITY 
        ORDER BY 2 DESC;
        """
        df9 = pd.read_sql(query, conn) 
        st.write(df9)
        st.bar_chart(df9, x= "city", y= "avg_price")
    elif question == "10. How are properties distributed across price buckets?":
        query = """
        SELECT 
    CASE 
        WHEN price < 100000 THEN 'Below 10Lakhs'
        WHEN price BETWEEN 100000 AND 300000 THEN '10 - 30Lakhs'
        WHEN price BETWEEN 300000 AND 500000 THEN '30 - 50Lakhs'
        WHEN price BETWEEN 500000 AND 1000000 THEN '50Lakhs - 1Crore'
        ELSE 'Above 1Crore'
        END AS price_bucket,
    
    COUNT(*) AS property_count
    FROM listings
    GROUP BY price_bucket
    ORDER BY property_count DESC;
        """
        df10 = pd.read_sql(query, conn) 
        st.write(df10)
    elif question == "11. What is the average days on market by city?":
        query = """
        SELECT l.city, CEIL(AVG(s.days_on_market)) AS avg_days_on_market
           FROM listings l JOIN sales s
           ON l.listing_id = s.listing_id
           GROUP BY 1;
        """
        df11 = pd.read_sql(query, conn) 
        st.write(df11)
    elif question == "12. Which property types sell the fastest?":
        query = """
        SELECT l.property_type , CEIL(AVG(s.date_sold - l.date_listed)) AS no_of_days
        FROM listings l join sales s
        ON l.listing_id = s.listing_id
        GROUP BY 1
        ORDER BY 2 ASC;
        """
        df12 = pd.read_sql(query, conn) 
        st.write(df12)
        st.write("TOWN HOUSE") 
    elif question == "13. What percentage of properties are sold above listing price?":
        query = """
        SELECT 
        ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM listings l JOIN sales s ON l.listing_id = s.listing_id),2)
        AS percentage_above_listing
        FROM listings l JOIN sales s 
        ON l.listing_id = s.listing_id
        WHERE s.sale_price > l.price;
        """
        df13 = pd.read_sql(query, conn) 
        st.write(df13) 
    elif question == "14. What is the sale-to-list price ratio by city?":
        query = """
        SELECT l.city, ROUND(AVG(s.sale_price / l.price),2) AS sale_to_list_price_ratio
        FROM listings l JOIN sales s
        ON l.listing_id = s.listing_id
        GROUP BY 1;
        """
        df14 = pd.read_sql(query, conn) 
        st.write(df14) 
    elif question == "15. Which listings took more than 90 days to sell?":
        query = """
        SELECT l.listing_id , CEIL(s.date_sold - l.date_listed) AS no_of_days
        from listings l join sales s
        ON l.listing_id = s.listing_id
        WHERE CEIL(s.date_sold - l.date_listed) > 90
        ORDER BY 2 ASC;
        """
        df15 = pd.read_sql(query, conn) 
        st.write(df15)
    elif question == "16. How does metro distance affect time on market?":
        query = """
        SELECT p.metro_distance_km, CEIL(AVG(s.days_on_market)) AS days_on_market
        FROM property p JOIN sales s 
        ON p.listing_id = s.listing_id
        GROUP BY 1
        ORDER BY 2 ASC;
        """
        df16 = pd.read_sql(query, conn) 
        st.write(df16)
    elif question == "17. What is the monthly sales trend?":
        query = """
        SELECT 
        EXTRACT(YEAR FROM date_sold) AS year,
        EXTRACT(MONTH FROM date_sold) AS month,
        COUNT(*) AS total_sales
        FROM sales 
        GROUP BY year, month
        ORDER BY year, month;
        """
        df17 = pd.read_sql(query, conn) 
        st.write(df17)
    elif question == "18. Which properties are currently unsold?":
        query = """
        SELECT l.listing_id
        FROM listings l LEFT JOIN sales s 
        ON l.listing_id = s.listing_id 
        WHERE s.date_sold IS NULL;
        """
        df18 = pd.read_sql(query, conn) 
        st.write(df18)
    elif question == "19. Which agents have closed the most sales?":
        query = """
        SELECT agent_id, name, deals_closed FROM agents
        ORDER BY 3 DESC 
        LIMIT 5;
        """
        df19 = pd.read_sql(query, conn) 
        st.write(df19)
    elif question == "20. Who are the top agents by total sales revenue?":
        query = """
        SELECT 
        a.agent_id,a.name,SUM(s.sale_price) AS total_revenue
        FROM agents a JOIN listings l 
        ON a.agent_id = l.agent_id
        JOIN sales s ON l.listing_id = s.listing_id
        GROUP BY a.agent_id, a.name
        ORDER BY total_revenue DESC;
        """
        df20 = pd.read_sql(query, conn) 
        st.write(df20)
    elif question == "21. Which agents close deals fastest?":
        query = """
        SELECT agent_id, name, avg_closing_days FROM agents
        ORDER BY 3 ASC;
        """
        df21 = pd.read_sql(query, conn) 
        st.write(df21)
    elif question == "22. Does experience correlate with deals closed?":
        query = """
        SELECT deals_closed, experience_years FROM agents
        ORDER BY 2 DESC;
        """
        df22 = pd.read_sql(query, conn) 
        st.write(df22) 
    elif question == "23. Do agents with higher ratings close deals faster?":
        query = """
        SELECT rating, avg_closing_days FROM agents
        ORDER BY 1 DESC;
        """
        df23 = pd.read_sql(query, conn) 
        st.write(df23)
    elif question == "24. What is the average commission earned by each agent?":
        query = """
        SELECT agent_id, commission_rate AS avg_commission FROM agents;
        """
        df24 = pd.read_sql(query, conn) 
        st.write(df24)
    elif question == "25. Which agents currently have the most active listings?":
        query = """
        SELECT 
           l.agent_id, COUNT(*) AS active_listings
           FROM listings l LEFT JOIN sales s 
           ON l.listing_id = s.listing_id
           WHERE s.listing_id IS NULL
           GROUP BY l.agent_id
           ORDER BY active_listings DESC;
        """
        df25 = pd.read_sql(query, conn) 
        st.write(df25)
    elif question == "26. What percentage of buyers are investors vs end users?":
        query = """
        SELECT 
                 ROUND((COUNT(CASE WHEN buyer_type = 'Investor' THEN 1 END) * 100.0) / COUNT(*), 2) AS perc_investors,
                 ROUND((COUNT(CASE WHEN buyer_type = 'End User' THEN 1 END) * 100.0) / COUNT(*), 2) AS perc_enduser
                 FROM buyers;
        """
        df26 = pd.read_sql(query, conn) 
        st.write(df26)
    elif question == "27. Which cities have the highest loan uptake rate?":
        query = """
        SELECT l.city,
        COUNT(CASE WHEN b.loan_taken = TRUE THEN 1 END) AS total_loans,
        ROUND(100.0 * SUM(CASE WHEN b.loan_taken = TRUE THEN 1 ELSE 0 END) / COUNT(*),2) AS loan_uptake_rate
        FROM buyers b
        JOIN sales s
        ON b.sale_id = s.listing_id
        JOIN listings l
        ON s.listing_id = l.listing_id
        GROUP BY l.city
        ORDER BY loan_uptake_rate DESC;
        """
        df27 = pd.read_sql(query, conn) 
        st.write(df27)
    elif question == "28. What is the average loan amount by buyer type?":
        query = """
        SELECT buyer_type, AVG(loan_amount) AS avg_loan_amt 
           FROM buyers
           WHERE loan_taken = 1
           GROUP BY 1;
        """
        df28 = pd.read_sql(query, conn) 
        st.write(df28)
    elif question == "29. Which payment mode is most commonly used?":
        query = """
        SELECT payment_mode, COUNT(payment_mode) FROM buyers
        GROUP BY 1 
        ORDER BY 2 DESC
        LIMIT 1;
        """
        df29 = pd.read_sql(query, conn) 
        st.write(df29)
    elif question == "30. Do loan-backed purchases take longer to close?":
        query = """
        SELECT b.loan_taken,
        ROUND(AVG(DATEDIFF(s.date_sold, l.date_listed)), 2) AS avg_days_to_close
        FROM buyers b JOIN sales s ON b.sale_id = s.listing_id
        JOIN listings l ON s.listing_id = l.listing_id
        GROUP BY b.loan_taken;
        """
        df30 = pd.read_sql(query, conn) 
        st.write(df30)
    elif question == "1. What is the average listing price by city?":
        query = """
        SELECT city, ROUND(AVG(price), 2) AS avg_price
        FROM listings
        GROUP BY city
        """
        df1 = pd.read_sql(query, conn) 
        st.write(df1) 
        st.bar_chart(df1, x= "city", y= "avg_price")   
    elif question == "2. What is the average price per square foot by property type?":
        query = """
        SELECT property_type, AVG(price/sqft) AS avg_price_per_sqft 
        FROM listings GROUP BY property_type
        """ 
        df2 = pd.read_sql(query, conn) 
        st.write(df2)


       
if page == "crud":
     option = st.radio("select the option: ", ["listings", "agents", "buyers", "sales", "property"], horizontal=True)
     if option == "listings":
        listings_opt = st.radio("select", ["view", "add", "update", "delete"], horizontal=True)
        if listings_opt == "view":
            query = "SELECT * FROM listings"
            tab1 = pd.read_sql(query, conn)
            st.write(tab1)

        elif listings_opt == "add":
            st.subheader(f"Add Record to listings")
            df = pd.read_sql("SELECT * FROM listings", conn)
            input_data = {}
            for col in df.columns:
                input_data[col] = st.text_input(f"Enter {col}")
                # if col == "listing_id":
                #     continue  # skip auto PK 
            if st.button("Insert", key=f"{option}_{listings_opt}_insert"):
                cols = ", ".join(input_data.keys())
                placeholders = ", ".join(["%s"] * len(input_data))
                query = f"INSERT INTO listings ({cols}) VALUES ({placeholders})"
                cur.execute(query, tuple(input_data.values()))
                conn.commit()
                st.success("Record Inserted")

        elif listings_opt == "update":
            st.subheader(f"Update Record in listings")
            df = pd.read_sql("SELECT * FROM listings", conn)
            if df.empty:
                st.warning("No records to update")
            else:
                selected_id = st.selectbox(f"Select listing_id ", df["listing_id"], key="listing_update_select")        
                selected_row = df[df["listing_id"] == selected_id].iloc[0]
                st.write("Current Data:", selected_row)
                update_data = {}
                for col in df.columns:
                    if col == "listing_id":
                        continue
                    update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))
                if st.button("Update"):
                    set_clause = ", ".join([f"{col}= %s" for col in update_data.keys()])
                    query = f"UPDATE listings SET {set_clause} WHERE listing_id = %s"
                    values = list(update_data.values()) + [selected_id]
                    cur.execute(query, values)
                    conn.commit()
                    st.success("Record Updated")
                    
                    
        elif listings_opt == "delete":
            st.subheader(f"🗑️ Delete Record from listings ")
            df = pd.read_sql(f"SELECT * FROM listings", conn)
            if df.empty:
                st.warning("No records to delete")
            else:
                selected_id = st.selectbox(f"Select listing_id to delete", df["listing_id"], key="delete_select")
                if st.button("Delete"):
                    query = "DELETE FROM listings WHERE listing_id = %s"
                    cur.execute(query, (selected_id,))
                    conn.commit()
                    st.success("Record Deleted") 

                    

     if option == "agents":
        agents_opt = st.radio("select", ["view", "add", "update", "delete"], horizontal=True)
        if agents_opt == "view":
            query = "SELECT * FROM agents"
            tab2 = pd.read_sql(query, conn)
            st.write(tab2)

        elif agents_opt == "add":
             st.subheader(f"Add Record to agents")
             df = pd.read_sql("SELECT * FROM agents", conn)
             input_data = {}
             for col in df.columns:
                 input_data[col] = st.text_input(f"Enter {col}")
             if st.button("Insert", key=f"{option}_{agents_opt}_insert"):
                cols = ", ".join(input_data.keys())
                placeholders = ", ".join(["%s"] * len(input_data))
                query = f"INSERT INTO agents ({cols}) VALUES ({placeholders})"
                cur.execute(query, tuple(input_data.values()))
                conn.commit()
                st.success("Record Inserted")

        elif agents_opt == "update":
            st.subheader(f"Update Record in agents")
            df = pd.read_sql("SELECT * FROM agents", conn)
            if df.empty:
                st.warning("No records to update")
            else:
                selected_id = st.selectbox(f"Select agent_id ", df["agent_id"], key="listing_update_select")        
                selected_row = df[df["agent_id"] == selected_id].iloc[0]
                st.write("Current Data:", selected_row)
                update_data = {}
                for col in df.columns:
                    if col == "agent_id":
                        continue
                    update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))
                if st.button("Update"):
                    set_clause = ", ".join([f"{col}=%s" for col in update_data.keys()])
                    query = f"UPDATE agents SET {set_clause} WHERE {"agent_id"}= %s"
                    values = list(update_data.values()) + [selected_id]
                    cur.execute(query, values)
                    conn.commit()
                    st.success("Record Updated")
                    
                    
        elif agents_opt == "delete":
            st.subheader(f"🗑️ Delete Record from agents ")
            df = pd.read_sql(f"SELECT * FROM agents", conn)
            if df.empty:
                st.warning("No records to delete")
            else:
                selected_id = st.selectbox(f"Select agent_id to delete", df["agent_id"], key="delete_select")
                if st.button("Delete"):
                    query = "DELETE FROM agents WHERE agent_id = %s"
                    cur.execute(query, (selected_id,))
                    conn.commit()
                    st.success("Record Deleted") 


     if option == "buyers":
        buyers_opt = st.radio("select", ["view", "add", "update", "delete"], horizontal=True)
        if buyers_opt == "view":
            query = "SELECT * FROM buyers"
            tab3 = pd.read_sql(query, conn)
            st.write(tab3)

        elif buyers_opt == "add":
             st.subheader(f"Add Record to buyers")
             df = pd.read_sql("SELECT * FROM buyers", conn)
             input_data = {}
             for col in df.columns:
                 input_data[col] = st.text_input(f"Enter {col}")
             if st.button("Insert", key=f"{option}_{buyers_opt}_insert"):
                cols = ", ".join(input_data.keys())
                placeholders = ", ".join(["%s"] * len(input_data))
                query = f"INSERT INTO buyers ({cols}) VALUES ({placeholders})"
                cur.execute(query, tuple(input_data.values()))
                conn.commit()
                st.success("Record Inserted")

        elif buyers_opt == "update":
            st.subheader(f"Update Record in buyers")
            df = pd.read_sql("SELECT * FROM buyers", conn)
            if df.empty:
                st.warning("No records to update")
            else:
                selected_id = st.selectbox(f"Select sale_id ", df["sale_id"], key="listing_update_select")        
                selected_row = df[df["sale_id"] == selected_id].iloc[0]
                st.write("Current Data:", selected_row)
                update_data = {}
                for col in df.columns:
                    if col == "sale_id":
                        continue
                    update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))
                if st.button("Update"):
                    set_clause = ", ".join([f"{col}= %s" for col in update_data.keys()])
                    query = f"UPDATE buyers SET {set_clause} WHERE {"sale_id"} = %s"
                    values = list(update_data.values()) + [selected_id]
                    cur.execute(query, values)
                    conn.commit()
                    st.success("Record Updated")
                    
                    
        elif buyers_opt == "delete":
            st.subheader(f"🗑️ Delete Record from buyers ")
            df = pd.read_sql(f"SELECT * FROM buyers", conn)
            if df.empty:
                st.warning("No records to delete")
            else:
                selected_id = st.selectbox(f"Select sale_id to delete", df["sale_id"], key="delete_select")
                if st.button("Delete"):
                    query = "DELETE FROM buyers WHERE sale_id = %s"
                    cur.execute(query, (selected_id,))
                    conn.commit()
                    st.success("Record Deleted")  


     if option == "sales":
        sales_opt = st.radio("select", ["view", "add", "update", "delete"], horizontal=True)
        if sales_opt == "view":
            query = "SELECT * FROM sales"
            tab4 = pd.read_sql(query, conn)
            st.write(tab4)

        elif sales_opt == "add":
             st.subheader(f"Add Record to sale ")
             df = pd.read_sql("SELECT * FROM sales", conn)
             input_data = {}
             for col in df.columns:
                 input_data[col] = st.text_input(f"Enter {col}")
             if st.button("Insert", key=f"{option}_{sales_opt}_insert"):
                cols = ", ".join(input_data.keys())
                placeholders = ", ".join(["%s"] * len(input_data))
                query = f"INSERT INTO sales ({cols}) VALUES ({placeholders})"
                cur.execute(query, tuple(input_data.values()))
                conn.commit()
                st.success("Record Inserted")

        elif sales_opt == "update":
            st.subheader(f"Update Record in sales ")
            df = pd.read_sql("SELECT * FROM sales", conn)
            if df.empty:
                st.warning("No records to update")
            else:
                selected_id = st.selectbox(f"Select listing_id ", df["listing_id"], key="listing_update_select")        
                selected_row = df[df["listing_id"] == selected_id].iloc[0]
                st.write("Current Data:", selected_row)
                update_data = {}
                for col in df.columns:
                    if col == "listing_id":
                        continue
                    update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))
                if st.button("Update"):
                    set_clause = ", ".join([f"{col}=%s" for col in update_data.keys()])
                    query = f"UPDATE sales SET {set_clause} WHERE {"listing_id"}= %s "
                    values = list(update_data.values()) + [selected_id]
                    cur.execute(query, values)
                    conn.commit()
                    st.success("Record Updated")                    
                    
        elif sales_opt == "delete":
            st.subheader(f"🗑️ Delete Record from sales ")
            df = pd.read_sql(f"SELECT * FROM sales", conn)
            if df.empty:
                st.warning("No records to delete")
            else:
                selected_id = st.selectbox(f"Select listing_id to delete", df["listing_id"], key="delete_select")
                if st.button("Delete"):
                    query = "DELETE FROM sales WHERE listing_id = %s"
                    cur.execute(query, (selected_id,))
                    conn.commit()
                    st.success("Record Deleted") 


     if option == "property":
        property_opt = st.radio("select", ["view", "add", "update", "delete"], horizontal=True)
        if property_opt == "view":
            query = "SELECT * FROM property"
            tab5 = pd.read_sql(query, conn)
            st.write(tab5)

        elif property_opt == "add":
             st.subheader(f"Add Record to  property ")
             df = pd.read_sql("SELECT * FROM property", conn)
             input_data = {}
             for col in df.columns:
                 input_data[col] = st.text_input(f"Enter {col}")
             if st.button("Insert", key=f"{option}_{property_opt}_insert"):
                cols = ", ".join(input_data.keys())
                placeholders = ", ".join(["%s"] * len(input_data))
                query = f"INSERT INTO property ({cols}) VALUES ({placeholders})"
                cur.execute(query, tuple(input_data.values()))
                conn.commit()
                st.success("Record Inserted")

        elif property_opt == "update":
            st.subheader(f"Update Record in property ")
            df = pd.read_sql("SELECT * FROM property", conn)
            if df.empty:
                st.warning("No records to update")
            else:
                selected_id = st.selectbox(f"Select listing_id ", df["listing_id"], key="listing_update_select")        
                selected_row = df[df["listing_id"] == selected_id].iloc[0]
                st.write("Current Data:", selected_row)
                update_data = {}
                for col in df.columns:
                    if col == "listing_id":
                        continue
                    update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))
                if st.button("Update"):
                    set_clause = ", ".join([f"{col}=%s" for col in update_data.keys()])
                    query = f"UPDATE property SET {set_clause} WHERE {"listing_id"}= %s"
                    values = list(update_data.values()) + [selected_id]
                    cur.execute(query, values)
                    conn.commit()
                    st.success("Record Updated")
                                        
        elif property_opt == "delete":
            st.subheader(f"🗑️ Delete Record from {property}")
            df = pd.read_sql(f"SELECT * FROM property", conn)
            if df.empty:
                st.warning("No records to delete")
            else:
                selected_id = st.selectbox(f"Select listing_id to delete", df["listing_id"], key="delete_select")
                if st.button("Delete"):
                    query = "DELETE FROM property WHERE listing_id = %s"
                    cur.execute(query, (selected_id,))
                    conn.commit()
                    st.success("Record Deleted") 
        


    #  elif option == "agents":
    #     query = "SELECT * FROM agents"
    #     tab2 = pd.read_sql(query, conn) 
    #     st.write(tab2)
    #  elif option == "buyers":
    #     query = "SELECT * FROM buyers"
    #     tab3 = pd.read_sql(query, conn) 
    #     st.write(tab3)
    #  elif option == "sales":
    #     query = "SELECT * FROM sales"
    #     tab4 = pd.read_sql(query, conn) 
    #     st.write(tab4)
    #  elif option == "property":
    #     query = "SELECT * FROM property"
    #     tab5 = pd.read_sql(query, conn) 
    #     st.write(tab5)
   





#ADD

# elif operation == "Add":
#     st.subheader(f"Add Record to {table_name}")

#     input_data = {}

#     for col in columns:
#         if col == pk_column:
#             continue  # skip auto PK
#         input_data[col] = st.text_input(f"Enter {col}")

#     if st.button("Insert"):
#         cols = ", ".join(input_data.keys())
#         placeholders = ", ".join(["?"] * len(input_data))

#         query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
#         cursor.execute(query, tuple(input_data.values()))
#         conn.commit()

#         st.success("Record Inserted")


# # UPDATE

# elif operation == "Update":
#     st.subheader(f"Update Record in {table_name}")

#     df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

#     if df.empty:
#         st.warning("No records to update")
#     else:
#         selected_id = st.selectbox(f"Select {pk_column}", df[pk_column])

#         selected_row = df[df[pk_column] == selected_id].iloc[0]
#         st.write("Current Data:", selected_row)

#         update_data = {}

#         for col in columns:
#             if col == pk_column:
#                 continue
#             update_data[col] = st.text_input(f"New value for {col}", str(selected_row[col]))

#         if st.button("Update"):
#             set_clause = ", ".join([f"{col}=?" for col in update_data.keys()])
#             query = f"UPDATE {table_name} SET {set_clause} WHERE {pk_column}=?"

#             values = list(update_data.values()) + [selected_id]

#             cursor.execute(query, values)
#             conn.commit()

#             st.success("Record Updated")


# # DELETE

# elif operation == "Delete":
#     st.subheader(f"🗑️ Delete Record from {table_name}")

#     df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

#     if df.empty:
#         st.warning("No records to delete")
#     else:
#         selected_id = st.selectbox(f"Select {pk_column} to delete", df[pk_column])

#         if st.button("Delete"):
#             query = f"DELETE FROM {table_name} WHERE {pk_column}=?"
#             cursor.execute(query, (selected_id,))
#             conn.commit()

#             st.success("Record Deleted")




# city  = input()
# input(city) = "?"    
# update listings set city = "mexico", price = 1200000, where listing_id =  l200045
#                  input("city") = "?", ;

# if page == "intro":
#   st.title("BRICK VIEW ") 
#   st.write(" ") 
# elif page == "filter": 
#   query ="SELECT city, (ROUND(AVG(price),2)) FROM listings GROUP BY city" 
#   df1 = pd.read_sql(query, conn) 
#   st.write(df1)
# elif page == "filter":
#   query = "SELECT property_type, AVG(price/sqft) AS avg_price_per_sqft FROM listings GROUP BY property_type" 
#   df2 = pd.read_sql(query, conn) 
#   st.write(df2)






  
  










