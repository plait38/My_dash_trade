import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pinotdb import connect

# ตั้งค่าเพื่อให้ dashboard ใช้พื้นที่เต็มหน้าจอ
st.set_page_config(page_title="DADS6005 Realtime Trade Dashboard", layout="wide")

# เพิ่ม title และคำบรรยาย
st.title("DADS6005 Realtime Trade Dashboard")
st.write("Real-time Trade Data Analysis with Interactive Visualizations")

# Function to connect to Druid
def create_connection():
    conn = connect(host='13.229.109.174', port=8099, path='/query/sql', scheme='http')
    return conn

# สร้างการเชื่อมต่อกับ Druid
conn = create_connection()

# Function to execute a query and return a DataFrame
def execute_query(query):
    curs = conn.cursor()
    curs.execute(query)
    result = curs.fetchall()
    return pd.DataFrame(result, columns=[desc[0] for desc in curs.description])

# Predefine symbols for reuse
symbols = execute_query("SELECT DISTINCT SYMBOL FROM enriched")['SYMBOL'].tolist()

# Query 1: Total Trade Value by Symbol and Side without any selection
st.header("Total Trade Value by Symbol and Side")
query1 = """
SELECT
  SYMBOL,
  SIDE,
  SUM(TOTAL_TRADE_VALUE) AS TOTAL_TRADE_VALUE
FROM
  enriched
GROUP BY
  SYMBOL, SIDE;
"""
df1 = execute_query(query1)
st.dataframe(df1)

# Arrange plots in rows with two columns
# Row 1 - Plot 1: Count of HIGH and LOW Value Trades by Gender
col1, col2 = st.columns(2)

with col1:
    st.subheader("Count of HIGH and LOW Value Trades by Gender")
    genders = execute_query("SELECT DISTINCT GENDER FROM trade_user")['GENDER'].tolist()
    categories = ['HIGH', 'LOW']
    selected_gender = st.multiselect("Select Gender:", genders, default=genders)
    selected_category = st.multiselect("Select Trade Category:", categories, default=categories)

    query2 = f"""
    SELECT
      GENDER,
      TRADE_CATEGORY,
      COUNT(*) AS VALUE_TRADE_COUNT
    FROM
      trade_user
    WHERE
      GENDER IN ({','.join([f"'{g}'" for g in selected_gender])})
      AND TRADE_CATEGORY IN ({','.join([f"'{c}'" for c in selected_category])})
    GROUP BY
      GENDER, TRADE_CATEGORY;
    """
    df2 = execute_query(query2)
    pivot_df2 = df2.pivot(index='TRADE_CATEGORY', columns='GENDER', values='VALUE_TRADE_COUNT')
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot_df2.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e'])
    for container in ax.containers:
        ax.bar_label(container)
    plt.xlabel('Trade Category')
    plt.ylabel('Value Trade Count')
    plt.title('Count of HIGH and LOW Value Trades by Gender')
    plt.legend(title='Gender')
    plt.xticks(rotation=0)
    st.pyplot(fig)

# Row 1 - Plot 2: Total Trade Value by Region and Gender
with col2:
    st.subheader("Total Trade Value by Region and Gender")
    regions = execute_query("SELECT DISTINCT REGIONID FROM trade_user")['REGIONID'].tolist()
    selected_region = st.multiselect("Select Region:", regions, default=regions)

    query3 = f"""
    SELECT
      REGIONID,
      GENDER,
      SUM(TOTAL_TRADE_VALUE) AS TOTAL_TRADE_VALUE
    FROM
      trade_user
    WHERE
      REGIONID IN ({','.join([f"'{r}'" for r in selected_region])})
    GROUP BY
      REGIONID, GENDER;
    """
    df3 = execute_query(query3)
    region_gender_data = df3.groupby(['REGIONID', 'GENDER'])['TOTAL_TRADE_VALUE'].sum().unstack()
    fig, ax = plt.subplots(figsize=(10, 6))
    region_gender_data.plot(kind='barh', ax=ax)
    plt.ylabel('Region ID')
    plt.xlabel('Total Trade Value')
    plt.title('Total Trade Value by Region and Gender')
    plt.legend(title='Gender')
    st.pyplot(fig)

# Row 2 - Plot 1: Average Price by Region and Symbol (Heatmap)
col3, col4 = st.columns(2)

with col3:
    st.subheader("Average Price by Region and Symbol (Heatmap)")
    selected_symbols_for_heatmap = st.multiselect("Select Symbols for Heatmap:", symbols, default=symbols)

    query4 = f"""
    SELECT
      REGIONID,
      SYMBOL,
      AVG(PRICE) AS AVG_PRICE
    FROM
      trade_user
    WHERE
      SYMBOL IN ({','.join([f"'{s}'" for s in selected_symbols_for_heatmap])})
    GROUP BY
      REGIONID, SYMBOL;
    """
    df4 = execute_query(query4)
    pivot_df4 = df4.pivot(index='REGIONID', columns='SYMBOL', values='AVG_PRICE')
    plt.figure(figsize=(8, 6))
    sns.heatmap(pivot_df4, annot=True, cmap='YlGnBu', fmt=".1f", cbar_kws={'label': 'Average Price'})
    plt.title('Average Price by Region and Symbol')
    plt.xlabel('Symbol')
    plt.ylabel('Region ID')
    st.pyplot(plt)

