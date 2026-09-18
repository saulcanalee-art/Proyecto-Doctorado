mediciones = [100, 23, 45, 12, 67, 89, 34]
promedio = sum(mediciones) / len(mediciones)

#compresion de listas: filtra y transforma los elementos de la lista
altas = [m for m in mediciones if m > promedio]
resultados_set = {m for m in mediciones if m > promedio}

print("Promedio de mediciones:", promedio)
print("Mediciones altas:", altas)
print("Resultados del conjunto:", resultados_set)