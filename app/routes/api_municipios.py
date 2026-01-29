"""
API REST para búsqueda de provincias y municipios.
Usado por dropdowns con búsqueda substring en formularios.
"""
from flask import Blueprint, jsonify, request
from app.models.municipios import Municipio
from sqlalchemy import func

bp = Blueprint('api_municipios', __name__, url_prefix='/api')


@bp.route('/provincias')
def buscar_provincias():
    """
    Búsqueda de provincias con substring match.
    
    Query params:
    - q: término de búsqueda (opcional)
    
    Returns:
        JSON: ["Sevilla", "Málaga", ...]
    
    Ejemplo:
        /api/provincias?q=la
        → ["Sevilla", "Málaga"]  (contienen 'la')
    """
    query = request.args.get('q', '').strip()
    
    # Query base: provincias únicas
    provincias_query = Municipio.query.with_entities(
        Municipio.provincia
    ).distinct().order_by(Municipio.provincia)
    
    # Filtro substring (case-insensitive)
    if query:
        provincias_query = provincias_query.filter(
            func.lower(Municipio.provincia).like(f'%{query.lower()}%')
        )
    
    provincias = [p.provincia for p in provincias_query.all()]
    
    return jsonify(provincias)


@bp.route('/municipios')
def buscar_municipios():
    """
    Búsqueda de municipios filtrados por provincia y término.
    
    Query params:
    - provincia: nombre provincia (obligatorio)
    - q: término de búsqueda (opcional)
    
    Returns:
        JSON: [{"id": 1, "nombre": "Sevilla", "codigo": "41091"}, ...]
    
    Ejemplo:
        /api/municipios?provincia=Sevilla&q=la
        → [{"id": 15, "nombre": "Alcalá de Guadaíra", ...}]
    """
    provincia = request.args.get('provincia', '').strip()
    query = request.args.get('q', '').strip()
    
    if not provincia:
        return jsonify({"error": "Parámetro 'provincia' requerido"}), 400
    
    # Query base: municipios de la provincia
    municipios_query = Municipio.query.filter_by(
        provincia=provincia
    ).order_by(Municipio.nombre)
    
    # Filtro substring (case-insensitive)
    if query:
        municipios_query = municipios_query.filter(
            func.lower(Municipio.nombre).like(f'%{query.lower()}%')
        )
    
    municipios = [
        {
            "id": m.id,
            "nombre": m.nombre,
            "codigo": m.codigo,
            "provincia": m.provincia
        }
        for m in municipios_query.all()
    ]
    
    return jsonify(municipios)
