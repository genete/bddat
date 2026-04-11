from flask import Blueprint, render_template

bp = Blueprint('demo', __name__, url_prefix='/demo')


@bp.route('/diagrama')
def diagrama():
    """POC React+Vite — diagrama interactivo árbol ESFTT. Spike #291."""
    return render_template('demo/diagrama.html')
