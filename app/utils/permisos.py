"""
Utilidades para control de permisos sobre expedientes.

Centraliza la lógica de acceso según roles para evitar duplicación
y facilitar el mantenimiento de las reglas de negocio.
"""
from flask import flash, redirect, url_for
from flask_login import current_user


def puede_acceder_expediente(expediente):
    """
    Verifica si el usuario actual puede acceder a un expediente.
    
    Reglas:
    - ADMIN/SUPERVISOR: Acceso total a todos los expedientes
    - TRAMITADOR/ADMINISTRATIVO: Solo sus expedientes asignados
    
    Args:
        expediente: Instancia del modelo Expediente
        
    Returns:
        bool: True si tiene acceso, False si no
    """
    # ADMIN y SUPERVISOR pueden acceder a cualquier expediente
    if current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        return True
    
    # Otros roles solo a expedientes donde son responsables
    return expediente.responsable_id == current_user.id


def puede_editar_expediente(expediente):
    """
    Verifica si el usuario actual puede editar un expediente.
    
    Actualmente usa las mismas reglas que puede_acceder_expediente,
    pero está separado por si en el futuro las reglas difieren
    (por ejemplo, permitir lectura pero no escritura).
    
    Args:
        expediente: Instancia del modelo Expediente
        
    Returns:
        bool: True si puede editar, False si no
    """
    return puede_acceder_expediente(expediente)


def puede_cambiar_responsable():
    """
    Verifica si el usuario actual puede cambiar el responsable de un expediente.
    
    Returns:
        bool: True si puede cambiar responsable, False si no
    """
    return current_user.tiene_rol('ADMIN', 'SUPERVISOR')


def verificar_acceso_expediente(expediente, accion='acceder'):
    """
    Verifica acceso y redirige con mensaje si no tiene permisos.
    
    Args:
        expediente: Instancia del modelo Expediente
        accion: Texto descriptivo de la acción ('acceder', 'ver', 'editar', etc.)
        
    Returns:
        None si tiene acceso, Response (redirect) si no tiene acceso
    """
    if not puede_acceder_expediente(expediente):
        flash(f'No tienes permisos para {accion} este expediente', 'danger')
        return redirect(url_for('expedientes.index'))
    return None
