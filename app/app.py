# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

from database import SessionLocal
from database import User
from database import PredictionHistory

# =========================================================
# DATABASE
# =========================================================

db = SessionLocal()

# =========================================================
# USER FUNCTIONS
# =========================================================

def get_user(username):

    return db.query(User).filter(
        User.username == username
    ).first()

def create_user(

    username,
    password,
    company,
    role,
    location,
    department

):

    new_user = User(

        username=username,
        password=password,
        company=company,
        role=role,
        location=location,
        department=department

    )

    db.add(new_user)
    db.commit()

def save_prediction(

    username,
    tenure,
    monthly_charges,
    total_charges,
    probability,
    risk

):

    prediction = PredictionHistory(

        username=username,
        tenure=tenure,
        monthly_charges=monthly_charges,
        total_charges=total_charges,
        probability=probability,
        risk=risk,
        prediction_date=str(datetime.now())

    )

    db.add(prediction)
    db.commit()

def get_prediction_history(username):

    return db.query(PredictionHistory).filter(
        PredictionHistory.username == username
    ).all()

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(

    page_title="Financial Operations Analytics",
    page_icon="📊",
    layout="wide"

)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI';
    background-color: #050816;
}

/* MAIN */
.main {
    background-color: #050816;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {

    background:
    linear-gradient(
        180deg,
        #081120,
        #0F172A
    );

    border-right:
    1px solid rgba(59,130,246,0.15);

    backdrop-filter: blur(18px);
}

/* CONTAINER */
.block-container {

    max-width: 1650px;

    padding-top: 2rem;

    padding-left: 2rem;

    padding-right: 2rem;

    margin: auto;
}
            
/* TITLES */
.big-title {
    font-size: 58px;
    font-weight: 800;
    color: white;
}

.subtitle {
    font-size: 22px;
    color: #94A3B8;
}

/* CARDS */
.card {

    background:
    linear-gradient(
        145deg,
        rgba(17,24,39,0.95),
        rgba(30,41,59,0.95)
    );

    padding: 28px;

    border-radius: 24px;

    border: 1px solid rgba(59,130,246,0.15);

    backdrop-filter: blur(14px);

    box-shadow:
    0 8px 32px rgba(0,0,0,0.35);

    transition: all 0.35s ease;

    overflow: hidden;

    position: relative;
}

.card:hover {

    transform: translateY(-6px);

    border: 1px solid rgba(59,130,246,0.45);

    box-shadow:

    0 0 25px rgba(37,99,235,0.25),
    0 12px 40px rgba(0,0,0,0.45);

}
/* PROFILE */
.profile-card {
    background: linear-gradient(145deg,#111827,#1E293B);
    padding: 35px;
    border-radius: 25px;
    border: 1px solid #1E293B;
    box-shadow: 0px 4px 25px rgba(0,0,0,0.35);
}

/* LOGIN */
.login-card {
    background: linear-gradient(145deg,#0F172A,#111827);
    padding: 40px;
    border-radius: 25px;
    border: 1px solid #1E293B;
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(135deg,#2563EB,#1D4ED8);
    color: white;
    border-radius: 12px;
    height: 3.3em;
    border: none;
    font-size: 17px;
    font-weight: bold;
    width: 100%;
}

.stButton>button:hover {
    background: linear-gradient(135deg,#1D4ED8,#1E40AF);
    color: white;
}

/* METRICS */
[data-testid="metric-container"] {
    background: linear-gradient(145deg,#111827,#1E293B);
    border: 1px solid #1E293B;
    padding: 20px;
    border-radius: 20px;
}

/* TABLE */
[data-testid="stDataFrame"] {
    background-color: #111827;
    border-radius: 20px;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# =========================================================
# LOGIN PAGE
# =========================================================

def login():

    st.markdown("""

    <div style='text-align:center; padding-top:40px;'>

    <h1 class='big-title'>
    📊 Financial Operations Analytics
    </h1>

    <p class='subtitle'>
    AI-Powered Enterprise Financial Intelligence Platform
    </p>

    </div>

    """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")

        st.write("")

        if st.button("🚀 Login"):

            user = get_user(username)

            if user and user.password == password:

                st.session_state.logged_in = True
                st.session_state.username = username

                st.success("✅ Login Successful")
                st.rerun()

            else:

                st.error("❌ Invalid Username or Password")

        st.write("")

        st.info("Demo Login → appu@gmail.com / Appu@2580")

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# SIGNUP PAGE
# =========================================================

def signup():

    st.title("📝 Create Enterprise Account")

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        username = st.text_input("👤 Email")
        password = st.text_input("🔒 Password", type="password")
        company = st.text_input("🏢 Company Name")

    with col2:

        role = st.text_input("💼 Role")
        location = st.text_input("📍 Location")
        department = st.text_input("🏛 Department")

    st.write("")

    if st.button("✅ Create Enterprise Account"):

        if get_user(username):

            st.error("❌ Account already exists")

        else:

            create_user(

                username,
                password,
                company,
                role,
                location,
                department

            )

            st.success("✅ Enterprise Account Created Successfully")

# =========================================================
# AUTH CHECK
# =========================================================

if not st.session_state.logged_in:

    auth = st.radio(
        "Select",
        ["Login", "Create Account"],
        horizontal=True
    )

    if auth == "Login":
        login()
    else:
        signup()

    st.stop()

# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load("models/churn_prediction_model.pkl")

# =========================================================
# USER DATA
# =========================================================

current_user = get_user(
    st.session_state.username
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("""

<h1 style='color:white; font-size:38px;'>
📊 FinAnalytics
</h1>

""", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.markdown(f"""

<div style="
background:#1E293B;
padding:20px;
border-radius:20px;
">

<h2 style='color:white;'>
{st.session_state.username}
</h2>

<p style='color:#CBD5E1;'>
{current_user.role}
</p>

<p style='color:#60A5FA;'>
{current_user.company}
</p>

</div>

""", unsafe_allow_html=True)

st.sidebar.write("")

page = st.sidebar.radio(

    "Navigation",

    [
        "Dashboard",
        "Predict Churn",
        "Prediction History",
        "Account Profile",
    ]

)

st.sidebar.write("")

st.sidebar.markdown("""

<div style="
background:linear-gradient(135deg,#2563EB,#1D4ED8);
padding:20px;
border-radius:20px;
color:white;
">

<h3>🚀 Enterprise Plan</h3>

✔ AI Prediction Engine  
✔ Customer Intelligence  
✔ Power BI Reports  
✔ Enterprise Analytics  
✔ Risk Detection Engine  
✔ Automated Insights  
✔ Executive Dashboard  

</div>

""", unsafe_allow_html=True)

st.sidebar.write("")

if st.sidebar.button("🚪 Logout"):

    st.session_state.logged_in = False
    st.rerun()

# =========================================================
# DASHBOARD PAGE
# =========================================================

if page == "Dashboard":

    st.markdown("""

    <div style='padding-bottom:25px;'>

    <h1 class='big-title'>
    Financial Operations Analytics
    </h1>

    <p class='subtitle'>
    AI-Powered Enterprise Financial Intelligence Platform
    </p>

    </div>

    """, unsafe_allow_html=True)

    # =====================================================
    # EXECUTIVE WELCOME
    # =====================================================

    st.markdown(f"""

    <div class='card'>

    <h2 style='color:white;'>
    Welcome Back, {st.session_state.username}
    </h2>

    <p style='color:#CBD5E1; font-size:18px;'>

    Enterprise Financial Intelligence Engine is active and monitoring
    customer behavior analytics in real-time.

    </p>

    </div>

    """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # =====================================================
    # KPI CARDS
    # =====================================================
    

    col1, col2, col3, col4 = st.columns(4)

    # =====================================================
    # REAL DATABASE KPI CALCULATIONS
    # =====================================================

    all_predictions = db.query(
        PredictionHistory
    ).all()

    total_predictions = len(all_predictions)

    high_risk_count = len([
        p for p in all_predictions
        if "HIGH" in p.risk
    ])

    if total_predictions > 0:

        avg_probability = sum(
            p.probability for p in all_predictions
        ) / total_predictions

        retention_rate = (1 - avg_probability) * 100

    else:

        avg_probability = 0
        retention_rate = 0

    # =====================================================
    # KPI DATA
    # =====================================================

    metrics = [

        (
            "Total Predictions",
            f"{total_predictions}"
        ),

        (
            "Retention Rate",
            f"{retention_rate:.1f}%"
        ),

        (
            "High Risk Customers",
            f"{high_risk_count}"
        ),

        (
            "AI Accuracy",
            "78.9%"
        )

    ]

    # =====================================================
    # KPI LOOP
    # =====================================================

    for col, metric in zip([col1, col2, col3, col4], metrics):

        with col:

            st.markdown(f"""

            <div class='card'>

            <h4 style='color:#94A3B8;'>
            {metric[0]}
            </h4>

            <h1 style='color:white;'>
            {metric[1]}
            </h1>

            </div>

            """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # =====================================================
    # CHARTS
    # =====================================================

    colA, colB, colC = st.columns([1,1,1], gap="large")

    # =====================================================
    # RETENTION ANALYSIS
    # =====================================================

    with colA:

        chart_data = pd.DataFrame({

            "Category": ["Retained", "Churned"],
            "Customers": [5174, 1869]

        })

        fig = px.pie(

            chart_data,
            names="Category",
            values="Customers",
            hole=0.70,
            title="Customer Retention Analysis"

        )

        fig.update_traces(
            textinfo="percent"
        )

        fig.update_layout(

            paper_bgcolor="#050816",
            plot_bgcolor="#050816",
            font_color="white",
            title_font_size=20,
            height=420,
            margin=dict(l=20, r=20, t=60, b=20)

        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    # =====================================================
    # REAL PREDICTION TREND
    # =====================================================

    with colB:

        history_data = db.query(
            PredictionHistory
        ).all()

        if len(history_data) > 0:

            history_df = pd.DataFrame([

                {
                    "date": item.prediction_date,
                    "risk": item.risk
                }

                for item in history_data

            ])

            history_df["date"] = pd.to_datetime(
                history_df["date"]
            )

            history_df["month"] = history_df[
                "date"
            ].dt.strftime("%b")

            trend_data = history_df.groupby(
                "month"
            ).size().reset_index(
                name="Predictions"
            )

        else:

            trend_data = pd.DataFrame({

                "month": ["No Data"],
                "Predictions": [0]

            })

        fig2 = px.line(

            trend_data,
            x="month",
            y="Predictions",
            markers=True,
            title="Prediction Growth Trend",
            template="plotly_dark",

        )

        fig2.update_traces(

            line=dict(
                width=4
            )

        )

        fig2.update_layout(

            paper_bgcolor="#050816",
            plot_bgcolor="#050816",
            font_color="white",
            title_font_size=20,
            height=420,

            xaxis=dict(
                showgrid=False
            ),

            yaxis=dict(
                gridcolor="#1E293B"
            ),

            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )

        )

        st.plotly_chart(
            fig2,
            width="stretch"
        )

    # =====================================================
    # RISK DISTRIBUTION
    # =====================================================

    with colC:

        risk_counts = {

            "LOW RISK": 0,
            "MEDIUM RISK": 0,
            "HIGH RISK": 0

        }

        for item in all_predictions:

            if "LOW" in item.risk:
                risk_counts["LOW RISK"] += 1

            elif "MEDIUM" in item.risk:
                risk_counts["MEDIUM RISK"] += 1

            elif "HIGH" in item.risk:
                risk_counts["HIGH RISK"] += 1

        risk_df = pd.DataFrame({

            "Risk": list(risk_counts.keys()),
            "Customers": list(risk_counts.values())

        })

        fig3 = px.bar(

            risk_df,
            x="Risk",
            y="Customers",
            title="Risk Distribution"

        )

        fig3.update_layout(

            paper_bgcolor="#050816",
            plot_bgcolor="#050816",
            font_color="white",
            title_font_size=20,
            height=420,

            yaxis=dict(
                gridcolor="#1E293B"
            ),

            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )

        )

        st.plotly_chart(
            fig3,
            width="stretch"
        )

    st.write("")
    st.write("")


    # =====================================================
    # REVENUE ANALYTICS
    # =====================================================

    st.subheader("📈 Enterprise Analytics Overview")

    analytics_data = pd.DataFrame({

        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Revenue": [12000, 18000, 22000, 28000, 35000, 42000]

    })

    fig3 = px.area(

        analytics_data,
        x="Month",
        y="Revenue",
        title="Revenue Growth Analytics"

    )

    fig3.update_layout(

        paper_bgcolor="#050816",
        plot_bgcolor="#050816",
        font_color="white"

    )

    st.plotly_chart(fig3, use_container_width="stretch")

    st.write("")
    st.write("")

    # =====================================================
    # EXECUTIVE AI INSIGHTS
    # =====================================================

    st.write("")
    st.write("")

    left_panel, right_panel = st.columns(
    [2,1],
    gap="large"
    )

    # =====================================================
    # AI INSIGHTS PANEL
    # =====================================================

    with left_panel:

     st.markdown("""

    <div class='card'>

    <h2 style='color:white; margin-bottom:25px;'>
    🧠 Executive AI Insights
    </h2>

    </div>

    """, unsafe_allow_html=True)

    insights = [

        (
            "📈 Revenue Performance",
            "Enterprise revenue growth increased by 18.4% compared to previous quarter."
        ),

        (
            "⚠ Retention Risk Analysis",
           f"{len([p for p in db.query(PredictionHistory).all() if 'HIGH' in p.risk])} customers currently fall under high-risk churn category."
        ),

        (
            "🧠 Predictive Forecast",
            "AI forecasting engine predicts stable retention performance over the next 90 days."
        ),

        (
            "💡 Strategic Recommendation",
            "Target medium-risk customers with personalized retention campaigns."
        ),

        (
            "📊 Analytics Infrastructure",
            "Real-time enterprise analytics engine operational across all services."
        )

    ]

    for title, desc in insights:

        st.markdown(f"""

        <div style="
        background:rgba(15,23,42,0.65);
        border:1px solid rgba(59,130,246,0.15);
        padding:22px;
        border-radius:18px;
        margin-bottom:18px;
        ">

        <h4 style='color:white; margin-bottom:10px;'>
        {title}
        </h4>

        <p style='color:#94A3B8; font-size:15px; line-height:1.6;'>
        {desc}
        </p>

        </div>

        """, unsafe_allow_html=True)

# =====================================================
# SYSTEM STATUS PANEL
# =====================================================

with right_panel:

    st.markdown("""

    <div class='card'>

    <h2 style='color:white; margin-bottom:25px;'>
    🚀 System Status
    </h2>

    <div style='margin-bottom:18px;'>
    <span style='color:#22C55E; font-size:18px;'>●</span>
    <span style='color:white;'> AI Engine Online</span>
    </div>

    <div style='margin-bottom:18px;'>
    <span style='color:#3B82F6; font-size:18px;'>●</span>
    <span style='color:white;'> Database Connected</span>
    </div>

    <div style='margin-bottom:18px;'>
    <span style='color:#F59E0B; font-size:18px;'>●</span>
    <span style='color:white;'> Analytics Active</span>
    </div>

    <div style='margin-bottom:18px;'>
    <span style='color:#A855F7; font-size:18px;'>●</span>
    <span style='color:white;'> Forecast Engine Running</span>
    </div>

    <hr style='border:1px solid #1E293B;'>

    <p style='color:#94A3B8; line-height:1.7;'>

    Enterprise monitoring system active.<br>
    Real-time AI analytics synchronized successfully.

    </p>

    </div>

      </div>

    """, unsafe_allow_html=True)

# =========================================================
# PREDICT CHURN PAGE
# =========================================================

if page == "Predict Churn":
    st.markdown("""

    <div class='card' style='padding:35px; margin-bottom:25px;'>

    <h1 style='color:white; margin-bottom:10px;'>
    🔍 Enterprise AI Risk Prediction
    </h1>

    <p style='color:#94A3B8; font-size:17px;'>
    AI-powered churn intelligence engine for enterprise analytics,
    customer retention forecasting, and executive risk monitoring.
    </p>

    </div>

    """, unsafe_allow_html=True)

    # =====================================================
    # INPUT SECTION
    # =====================================================

    st.markdown("""
    <div class='card'>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:

        tenure = st.slider(
            "📅 Customer Tenure",
            0,
            72,
            12
        )

    with col2:

        monthly_charges = st.number_input(
            "💳 Monthly Charges",
            0.0,
            200.0,
            70.0
        )

    with col3:

        total_charges = st.number_input(
            "💰 Total Charges",
            0.0,
            10000.0,
            1000.0
        )

    st.write("")
    st.write("")

    predict_col1, predict_col2, predict_col3 = st.columns([1,1,1])

    with predict_col2:

        predict_button = st.button(
            "🚀 Run Enterprise AI Prediction"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    # PREDICTION ENGINE
    # =====================================================

    if predict_button:

        input_data = pd.DataFrame({

            "tenure": [tenure],
            "MonthlyCharges": [monthly_charges],
            "TotalCharges": [total_charges]

        })

        missing_cols = model.feature_names_in_

        for col in missing_cols:

            if col not in input_data.columns:
                input_data[col] = 0

        input_data = input_data[missing_cols]

        prediction = model.predict(input_data)[0]

        probability = model.predict_proba(
            input_data
        )[0][1]

        # =================================================
        # RISK LEVELS
        # =================================================

        if probability > 0.7:
            risk = "🔴 HIGH RISK"

        elif probability > 0.4:
            risk = "🟡 MEDIUM RISK"

        else:
            risk = "🟢 LOW RISK"

        # =================================================
        # EXECUTIVE METRICS
        # =================================================

        st.write("")
        st.write("")

        metric1, metric2, metric3 = st.columns(3)

        with metric1:

            st.markdown(f"""

            <div class='card'>

            <h4 style='color:#94A3B8;'>
            Churn Probability
            </h4>

            <h1 style='color:white;'>
            {probability:.2%}
            </h1>

            </div>

            """, unsafe_allow_html=True)

        with metric2:

            st.markdown(f"""

            <div class='card'>

            <h4 style='color:#94A3B8;'>
            Risk Level
            </h4>

            <h1 style='color:white;'>
            {risk}
            </h1>

            </div>

            """, unsafe_allow_html=True)

        with metric3:

            st.markdown(f"""

            <div class='card'>

            <h4 style='color:#94A3B8;'>
            Retention Score
            </h4>

            <h1 style='color:white;'>
            {(1 - probability):.2%}
            </h1>

            </div>

            """, unsafe_allow_html=True)

        st.write("")
        st.write("")

        # =================================================
        # GAUGE CHART
        # =================================================

        gauge = go.Figure(go.Indicator(

            mode="gauge+number",

            value=probability * 100,

            title={
                'text': "Enterprise Risk Score"
            },

            gauge={

                'axis': {
                    'range': [0, 100]
                },

                'bar': {
                    'color': "#2563EB"
                },

                'steps': [

                    {
                        'range': [0, 40],
                        'color': "#065F46"
                    },

                    {
                        'range': [40, 70],
                        'color': "#92400E"
                    },

                    {
                        'range': [70, 100],
                        'color': "#991B1B"
                    }

                ]

            }

        ))

        gauge.update_layout(

            paper_bgcolor="#050816",
            plot_bgcolor="#050816",
            font_color="white",
            height=450

        )

        st.plotly_chart(
            gauge,
            width="stretch"
        )

        # =================================================
        # AI RESULT MESSAGE
        # =================================================

        if prediction == 1:

            st.error(
                f"⚠️ Customer is likely to CHURN with probability {probability:.2%}"
            )

        else:

            st.success(
                f"✅ Customer is likely to STAY with retention probability {(1-probability):.2%}"
            )

        # =================================================
        # SAVE HISTORY
        # =================================================

        save_prediction(

            st.session_state.username,
            tenure,
            monthly_charges,
            total_charges,
            probability,
            risk

        )

# =========================================================
# HISTORY PAGE
# =========================================================

elif page == "Prediction History":

    st.title("📜 Enterprise Prediction History")

    user_history = get_prediction_history(
        st.session_state.username
    )

    if len(user_history) == 0:

        st.info("No prediction history available")

    else:

        df = pd.DataFrame([{

            "Date": item.prediction_date,
            "Tenure": item.tenure,
            "Monthly Charges": item.monthly_charges,
            "Total Charges": item.total_charges,
            "Probability": item.probability,
            "Risk": item.risk

        } for item in user_history])

        st.dataframe(
            df,
            width="stretch"
        )

        st.write("")

        # =====================================================
        # CSV DOWNLOAD
        # =====================================================

        csv = df.to_csv(index=False)

        st.download_button(

            "⬇ Download CSV Report",
            csv,
            file_name="prediction_history.csv",
            mime="text/csv"

        )

        # =====================================================
        # EXCEL DOWNLOAD
        # =====================================================

        excel_file = "enterprise_report.xlsx"

        df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as file:

            st.download_button(

                label="📥 Download Excel Report",
                data=file,
                file_name="enterprise_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            )

        st.write("")

        # =====================================================
        # RISK DISTRIBUTION
        # =====================================================

        risk_count = df["Risk"].value_counts()

        fig = px.bar(

            x=risk_count.index,
            y=risk_count.values,
            title="Risk Distribution"

        )

        fig.update_layout(

            paper_bgcolor="#050816",
            plot_bgcolor="#050816",
            font_color="white"

        )

        st.plotly_chart(fig, use_container_width="stretch")

# =========================================================
# PROFILE PAGE
# =========================================================

elif page == "Account Profile":

    st.title("👤 Enterprise Account Profile")

    st.write("")

    # =====================================================
    # PROFILE HEADER
    # =====================================================

    col1, col2 = st.columns([8,1])

    with col1:

        st.markdown(f"""

        <div class='profile-card'>

        <div style='display:flex; align-items:center;'>

        <div style="
        width:100px;
        height:100px;
        border-radius:50%;
        background:#2563EB;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:42px;
        color:white;
        font-weight:bold;
        margin-right:25px;
        ">

        {st.session_state.username[0].upper()}

        </div>

        <div>

        <h1 style='color:white; margin:0;'>
        {current_user.username}
        </h1>

        <p style='color:#CBD5E1; font-size:20px;'>
        {current_user.role}
        </p>

        <p style='color:#60A5FA;'>
        {current_user.company}
        </p>

        </div>

        </div>

        <hr style='margin:30px 0px; border:1px solid #1E293B;'>

        <div style='display:grid; grid-template-columns:1fr 1fr; gap:20px;'>

        <div>

        <p style='color:#9CA3AF;'>Department</p>

        <h3 style='color:white;'>
        {current_user.department}
        </h3>

        <p style='color:#9CA3AF;'>Employee ID</p>

        <h3 style='color:white;'>
        FIN-2026-991
        </h3>

        </div>

        <div>

        <p style='color:#9CA3AF;'>Location</p>

        <h3 style='color:white;'>
        {current_user.location}
        </h3>

        <p style='color:#9CA3AF;'>Enterprise Account</p>

        <h3 style='color:white;'>
        Premium Active
        </h3>

        </div>

        </div>

        </div>

        """, unsafe_allow_html=True)

    with col2:

        if st.button("✏️ Edit"):
            st.session_state.edit_mode = True

    st.write("")
    st.write("")

    # =====================================================
    # METRICS
    # =====================================================

    colA, colB, colC = st.columns(3)

    with colA:
        st.metric("Predictions Generated", "1,284")

    with colB:
        st.metric("Retention Rate", "91%")

    with colC:
        st.metric("AI Accuracy", "78.9%")

    # =====================================================
    # EDIT MODE
    # =====================================================

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if st.session_state.edit_mode:

        st.write("")
        st.write("")

        st.markdown("""
        <div class='profile-card'>
        <h2 style='color:white;'>⚙️ Edit Account Details</h2>
        <p style='color:#94A3B8;'>
        Update your enterprise profile information
        </p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        col1, col2 = st.columns(2)

        with col1:

            updated_username = st.text_input(
                "👤 Username / Email",
                value=current_user.username
            )

            updated_company = st.text_input(
                "🏢 Company Name",
                value=current_user.company
            )

            updated_role = st.text_input(
                "💼 Role",
                value=current_user.role
            )

            updated_department = st.text_input(
                "🏛 Department",
                value=current_user.department
            )

        with col2:

            updated_location = st.text_input(
                "📍 Location",
                value=current_user.location
            )

            updated_password = st.text_input(
                "🔒 Password",
                value=current_user.password,
                type="password"
            )

        st.write("")

        save_col, cancel_col = st.columns(2)

        with save_col:

            if st.button("💾 Save Changes"):

                old_username = current_user.username

                current_user.username = updated_username
                current_user.company = updated_company
                current_user.role = updated_role
                current_user.department = updated_department
                current_user.location = updated_location
                current_user.password = updated_password

                # UPDATE HISTORY USERNAME
                history_records = db.query(
                    PredictionHistory
                ).filter(
                    PredictionHistory.username == old_username
                ).all()

                for record in history_records:
                    record.username = updated_username

                db.commit()

                st.session_state.username = updated_username
                st.session_state.edit_mode = False

                st.success("✅ Account Updated Successfully")
                st.rerun()

        with cancel_col:

            if st.button("❌ Cancel"):
                st.session_state.edit_mode = False
                st.rerun()

# =========================================================
# FOOTER
# =========================================================

st.write("---")

st.caption(
    "Developed using Python, Streamlit, Plotly, Machine Learning & Power BI"
)