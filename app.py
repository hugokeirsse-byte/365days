from flask import Flask, render_template
from data import PLANTS # On importe ta liste de 365 plantes

app = Flask(__name__)

@app.route('/')
def index():
    # Cette fonction envoie la liste des plantes au fichier HTML
    return render_template('index.html', plants=PLANTS)

if __name__ == '__main__':
    app.run(debug=True)
