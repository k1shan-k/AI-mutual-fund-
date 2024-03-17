from flask import Flask, request, jsonify
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# Load the dataset
data = pd.read_csv("mutual_funds_data.csv")

# Replace '-' with NaN in numerical columns
numerical_cols = ['min_sip', 'min_lumpsum', 'expense_ratio', 'fund_size_cr', 'fund_age_yr', 
                  'sortino', 'alpha', 'sd', 'beta', 'sharpe', 'risk_level']
data[numerical_cols] = data[numerical_cols].replace('-', pd.NA)

# Drop rows with missing values
data.dropna(inplace=True)

# Define features and target variable
X = data.drop(columns=['returns_1yr', 'returns_3yr', 'returns_5yr'])
y = data['returns_5yr']  # Target variable (you can change this to returns_3yr or returns_5yr)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define categorical and numerical columns
categorical_cols = ['fund_manager', 'amc_name', 'rating', 'category', 'sub_category']
numerical_cols = ['min_sip', 'min_lumpsum', 'expense_ratio', 'fund_size_cr', 'fund_age_yr', 
                  'sortino', 'alpha', 'sd', 'beta', 'sharpe', 'risk_level']

# Preprocessing for numerical data
numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean'))
])

# Preprocessing for categorical data
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Bundle preprocessing for numerical and categorical data
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols)
    ])

# Define the model
model = RandomForestRegressor(n_estimators=100, random_state=42)

# Create and evaluate the pipeline
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                           ('model', model)
                          ])

# Train the model
pipeline.fit(X_train, y_train)

# Flask Application
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Welcome to Mutual Fund Returns Forecasting"

@app.route('/forecast', methods=['POST'])
def forecast_returns():
    scheme_name = request.json.get('scheme_name')
    if scheme_name is None:
        return jsonify({"error": "Scheme name is required"}), 400
    
    mutual_fund_data = data[data['scheme_name'] == scheme_name]
    if mutual_fund_data.empty:
        return jsonify({"error": "Scheme not found"}), 404
    
    input_data = mutual_fund_data.drop(columns=['returns_1yr', 'returns_3yr', 'returns_5yr'])
    forecasted_returns = pipeline.predict(input_data) + 1.79
    
    return jsonify({"scheme_name": scheme_name, "forecasted_returns": forecasted_returns.tolist()}), 200

if __name__ == '__main__':
    app.run(debug=True
