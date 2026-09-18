class Medicion:
    def __init__(self, valor: float, unidad: str):
        # Atributos protegidos por convención (_)
        self._valor = valor
        self._unidad = unidad

    @property
    def valor(self):
        """Property de solo lectura: expone el dato sin permitir reasignación directa."""
        return self._valor

    @property
    def unidad(self):
        return self._unidad

    def es_valida(self) -> bool:
        """Regresa True si el valor es un número estrictamente positivo."""
        return self._valor > 0


# Instancias de prueba
m1 = Medicion(valor=30.0, unidad="°C")
m1.valor = 30.0
m2 = Medicion(valor=-4.2, unidad="V")
# Pruebas de lectura y validación
print(f"Medición 1 ({m1.valor} {m1.unidad}) es válida: {m1.es_valida()}")
print(f"Medición 2 ({m2.valor} {m2.unidad}) es válida: {m2.es_valida()}")

# Demostración de solo lectura:
# Intentar ejecutar `m1.valor = 30.0` lanzará:
# AttributeError: property 'valor' of 'Medicion' object has no setter