"""Tests unitarios de _OPERADORES — issue #341 sesión 1."""
import pytest
from app.services.operadores import _OPERADORES


# EQ
def test_eq_igual():
    assert _OPERADORES['EQ']('VENCIDO', 'VENCIDO') is True

def test_eq_distinto():
    assert _OPERADORES['EQ']('EN_PLAZO', 'VENCIDO') is False


# NEQ
def test_neq_distinto():
    assert _OPERADORES['NEQ']('EN_PLAZO', 'VENCIDO') is True

def test_neq_igual():
    assert _OPERADORES['NEQ']('VENCIDO', 'VENCIDO') is False


# IN
def test_in_en_lista():
    assert _OPERADORES['IN']('VENCIDO', ['PROXIMO_VENCER', 'VENCIDO']) is True

def test_in_fuera_de_lista():
    assert _OPERADORES['IN']('EN_PLAZO', ['PROXIMO_VENCER', 'VENCIDO']) is False

def test_in_valor_unico_como_ref():
    """ref es string, no lista — debe funcionar igual que ref=['VENCIDO']."""
    assert _OPERADORES['IN']('VENCIDO', 'VENCIDO') is True


# NOT_IN
def test_not_in_fuera():
    assert _OPERADORES['NOT_IN']('EN_PLAZO', ['PROXIMO_VENCER', 'VENCIDO']) is True

def test_not_in_dentro():
    assert _OPERADORES['NOT_IN']('VENCIDO', ['PROXIMO_VENCER', 'VENCIDO']) is False


# IS_NULL
def test_is_null_con_none():
    assert _OPERADORES['IS_NULL'](None, None) is True

def test_is_null_con_valor():
    assert _OPERADORES['IS_NULL']('algo', None) is False


# NOT_NULL
def test_not_null_con_valor():
    assert _OPERADORES['NOT_NULL']('algo', None) is True

def test_not_null_con_none():
    assert _OPERADORES['NOT_NULL'](None, None) is False


# GT
def test_gt_mayor():
    assert _OPERADORES['GT'](10, 5) is True

def test_gt_igual():
    assert _OPERADORES['GT'](5, 5) is False

def test_gt_none_falla_silenciosamente():
    assert _OPERADORES['GT'](None, 5) is False


# GTE
def test_gte_mayor():
    assert _OPERADORES['GTE'](10, 5) is True

def test_gte_igual():
    assert _OPERADORES['GTE'](5, 5) is True

def test_gte_menor():
    assert _OPERADORES['GTE'](3, 5) is False


# LT
def test_lt_menor():
    assert _OPERADORES['LT'](3, 5) is True

def test_lt_igual():
    assert _OPERADORES['LT'](5, 5) is False

def test_lt_none_falla_silenciosamente():
    assert _OPERADORES['LT'](None, 5) is False


# LTE
def test_lte_menor():
    assert _OPERADORES['LTE'](3, 5) is True

def test_lte_igual():
    assert _OPERADORES['LTE'](5, 5) is True

def test_lte_mayor():
    assert _OPERADORES['LTE'](7, 5) is False


# BETWEEN
def test_between_dentro():
    assert _OPERADORES['BETWEEN'](5, [1, 10]) is True

def test_between_en_extremo():
    assert _OPERADORES['BETWEEN'](1, [1, 10]) is True
    assert _OPERADORES['BETWEEN'](10, [1, 10]) is True

def test_between_fuera():
    assert _OPERADORES['BETWEEN'](0, [1, 10]) is False

def test_between_none_falla_silenciosamente():
    assert _OPERADORES['BETWEEN'](None, [1, 10]) is False


# NOT_BETWEEN
def test_not_between_fuera():
    assert _OPERADORES['NOT_BETWEEN'](0, [1, 10]) is True

def test_not_between_dentro():
    assert _OPERADORES['NOT_BETWEEN'](5, [1, 10]) is False

def test_not_between_none_falla_silenciosamente():
    assert _OPERADORES['NOT_BETWEEN'](None, [1, 10]) is False
