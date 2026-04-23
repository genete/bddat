# -*- coding: utf-8 -*-
"""
Seed de catalogo_variables para el motor de reglas (paso 4).

Registra las 5 variables identificadas en el primer sprint del motor.
Idempotente: upsert por nombre (UNIQUE). No toca registros existentes
con distinto nombre.

Uso:
    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe scripts/seed_motor_variables.py
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.motor_reglas import CatalogoVariable

VARIABLES = [
    {
        'nombre':    'fase_ip_finalizada',
        'etiqueta':  'Fase IP finalizada (o existente)',
        'tipo_dato': 'boolean',
        'activa':    False,  # activar cuando exista la función en el Variable Registry
    },
    {
        'nombre':    'tramite_publicar_existe',
        'etiqueta':  'Trámite PUBLICAR existe en fase RESOLUCIÓN',
        'tipo_dato': 'boolean',
        'activa':    False,
    },
    {
        'nombre':    'sin_linea_aerea',
        'etiqueta':  'Sin línea aérea (instalación íntegramente subterránea)',
        'tipo_dato': 'boolean',
        'activa':    False,
    },
    {
        'nombre':    'max_tension_nominal_kv',
        'etiqueta':  'Tensión nominal máxima (kV)',
        'tipo_dato': 'numerico',
        'activa':    False,
    },
    {
        'nombre':    'solo_suelo_urbano_urbanizable',
        'etiqueta':  'Recorrido íntegro en suelo urbano o urbanizable',
        'tipo_dato': 'boolean',
        'activa':    False,
    },
]

app = create_app()

with app.app_context():
    creadas = 0
    for data in VARIABLES:
        existente = CatalogoVariable.query.filter_by(nombre=data['nombre']).first()
        if existente:
            print(f'  ya existe: {data["nombre"]}')
            continue
        variable = CatalogoVariable(
            nombre=data['nombre'],
            etiqueta=data['etiqueta'],
            tipo_dato=data['tipo_dato'],
            norma_id=None,
            activa=data['activa'],
        )
        db.session.add(variable)
        creadas += 1
        print(f'  creada:    {data["nombre"]}')

    db.session.commit()
    print(f'\nSeed completado: {creadas} variables creadas.')
