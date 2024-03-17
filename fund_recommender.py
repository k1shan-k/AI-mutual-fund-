from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load mutual funds data from CSV file
def load_mutual_funds_data(file_path):
    return pd.read_csv(file_path)

# Filter funds based on tenure and amount
def filter_funds(mutual_funds_data, tenure, amount):
    return mutual_funds_data[(mutual_funds_data['min_sip'] <= tenure) & (mutual_funds_data['min_lumpsum'] <= amount)]

# Rank funds based on risk-adjusted returns, rating, and other metrics
def rank_funds(filtered_funds):
    filtered_funds.loc[:, 'risk_adjusted_returns'] = filtered_funds['returns_5yr'] / filtered_funds['risk_level']
    filtered_funds.loc[:, 'rating_score'] = filtered_funds['rating'] / 5  # Normalizing rating to 0-1 range
    # Higher weightage to returns and rating
    filtered_funds.loc[:, 'weighted_score'] = 0.6 * filtered_funds['risk_adjusted_returns'] + 0.4 * filtered_funds['rating_score']
    return filtered_funds.sort_values(by='weighted_score', ascending=False)

# Recommend mutual funds based on tenure, amount, and rating
def recommend_mutual_funds(mutual_funds_data, tenure, amount):
    filtered_funds = filter_funds(mutual_funds_data, tenure, amount)
    ranked_funds = rank_funds(filtered_funds)
    return ranked_funds

# Calculate percentage allocation for each fund
def calculate_allocation(recommended_funds, total_investment_amount, tenure):
    recommended_funds['allocation_percentage'] = (recommended_funds['min_lumpsum'] / total_investment_amount) * 100
    total_percent = recommended_funds['allocation_percentage'].sum()
    recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'] / total_percent * 100
    # Adjust risk preference based on tenure ranges
    if tenure <= 3:
        recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'] * 0.6  # Prefer safer funds for tenure 1-3 years
    elif tenure <= 10:
        recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'] * 0.8  # Use a mix of different risk levels for tenure 4-10 years
    else:
        recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'] * 0.9  # Use a mix of different risk levels for tenure > 10 years
    # Ensure minimum allocated percentage is more than 1
    recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'].apply(lambda x: x if x > 1 else 1)
    # Adjust allocation percentages based on ratings
    recommended_funds['allocation_percentage'] = recommended_funds['rating'] / recommended_funds['rating'].sum() * recommended_funds['allocation_percentage'].sum()
    total_percent = recommended_funds['allocation_percentage'].sum()
    recommended_funds['allocation_percentage'] = recommended_funds['allocation_percentage'] / total_percent * 100
    return recommended_funds

@app.route('/recommend', methods=['POST'])
def recommend():
    content = request.json
    tenure = content['tenure']
    amount = content['amount']
    mutual_funds_data = load_mutual_funds_data("mutual_funds_data.csv")
    recommended_funds = recommend_mutual_funds(mutual_funds_data, tenure, amount)
    total_investment_amount = min(amount, recommended_funds['min_lumpsum'].sum())
    recommended_funds = calculate_allocation(recommended_funds, total_investment_amount, tenure)
    # Filter funds with allocation percentage more than 1%
    filtered_results = recommended_funds[recommended_funds['allocation_percentage'] > 1][['scheme_name', 'allocation_percentage']]
    return jsonify(filtered_results.to_dict(orient='records'))

if __name__ == "__main__":
    app.run(debug=True)
