import streamlit as st
import pandas as pd
import joblib

# Load trained model
model = joblib.load("models/churn_prediction_model.pkl")

# App title
st.title("Financial Operations Analytics")

st.subheader("Customer Churn Prediction System")

st.write("Enter customer details below to predict churn probability.")

# User inputs
tenure = st.slider("Tenure (Months)", 0, 72, 12)

monthly_charges = st.number_input(
    "Monthly Charges",
    min_value=0.0,
    max_value=200.0,
    value=70.0
)

total_charges = st.number_input(
    "Total Charges",
    min_value=0.0,
    max_value=10000.0,
    value=1000.0
)

# Prediction button
if st.button("Predict Churn"):

    # Create dataframe
    input_data = pd.DataFrame({
        'tenure': [tenure],
        'MonthlyCharges': [monthly_charges],
        'TotalCharges': [total_charges]
    })

    # Add missing columns
    missing_cols = model.feature_names_in_

    for col in missing_cols:
        if col not in input_data.columns:
            input_data[col] = 0

    input_data = input_data[missing_cols]

    # Prediction
    prediction = model.predict(input_data)[0]

    probability = model.predict_proba(input_data)[0][1]

    # Output
    if prediction == 1:
        st.error(f"Customer is likely to churn. Probability: {probability:.2f}")
    else:
        st.success(f"Customer is likely to stay. Probability: {probability:.2f}")