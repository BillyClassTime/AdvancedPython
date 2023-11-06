from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/hello-world')
def saludar():
    return jsonify({"mensaje": "Hola mundo"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)