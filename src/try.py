def convertir_y_dividir(texto, divisor=1):
    """
    Intenta convertir el texto a float y dividirlo entre el divisor.
    Retorna None si la conversión falla o si ocurre división entre cero.
    """
    try:
        numero = float(texto)
        return numero / divisor
    except ValueError:
        return None
    except ZeroDivisionError:
        return None


# Pruebas con las 3 entradas solicitadas
entradas = ["42.5", "", "palabra"]

for valor in entradas:
    resultado = convertir_y_dividir(valor)
    print(f"Entrada: {valor!r:<10} -> Resultado: {resultado}")

# Prueba adicional para ZeroDivisionError
div_cero = convertir_y_dividir("10.0", divisor=0)
print(f"Entrada: '10.0' / 0  -> Resultado: {div_cero}")