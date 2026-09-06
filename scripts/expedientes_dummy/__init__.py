"""Expedientes-tipo: escenarios de tramitación reproducibles.

Cada módulo construye un expediente completo por el circuito real de la
aplicación (servicios y endpoints, nunca INSERT sueltos). Se ejecutan como
programa contra la base de desarrollo, y la semilla de la base de tests los
invoca con `main(app, efectos_desarrollo=False)` (#849).
"""
