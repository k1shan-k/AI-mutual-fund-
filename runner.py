from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

recommend_url = "http://65.2.161.64/recommend"
scheme_url = "http://65.0.124.4/forecast"

@app.route('/get_forecasts', methods=['POST'])
def get_forecasts():
    try:
        # Get tenure and amount from the POST request
        tenure = int(request.json.get('tenure'))
        amount = float(request.json.get('amount'))

        # Request data for the first POST request
        data = {
            "tenure": tenure,
            "amount": amount
        }

        # Making first POST request to get scheme recommendations
        response_recommend = requests.post(recommend_url, json=data)

        # Check if the first request was successful (status code 200)
        if response_recommend.status_code == 200:
            # Extracting scheme names from JSON response
            schemes = [item['scheme_name'] for item in response_recommend.json()]
            forecasts = {}

            # Making another POST request for each scheme name
            for scheme_name in schemes:
                scheme_data = {"scheme_name": scheme_name}
                response_scheme = requests.post(scheme_url, json=scheme_data)

                # Check if the request was successful
                if response_scheme.status_code == 200:
                    forecasts[scheme_name] = response_scheme.json()
                else:
                    forecasts[scheme_name] = f"Error: {response_scheme.status_code}"

            return jsonify(forecasts)
        else:
            return jsonify({"error": f"Error: {response_recommend.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
