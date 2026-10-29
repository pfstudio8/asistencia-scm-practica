from main import registrar_asistencia, obtener_reporte_estadistico

# Test 1: Registro exitoso con DNI válido (>= 7 dígitos numéricos)
def test_registrar_asistencia_dni_valido():
    resultado = registrar_asistencia({"dni": "40123456", "materia": "Programación III"})
    assert resultado is True

# Test 2: Registro exitoso con DNI que contiene espacios en blanco (.strip())
def test_registrar_asistencia_dni_con_espacios():
    resultado = registrar_asistencia({"dni": "  40123456  ", "materia": "Programación III"})
    assert resultado is True

# Test 3: Rechazo por DNI con longitud menor a 7 dígitos
def test_registrar_asistencia_dni_corto():
    resultado = registrar_asistencia({"dni": "12345", "materia": "Programación III"})
    assert resultado is False

# Test 4: Rechazo por DNI con caracteres no numéricos
def test_registrar_asistencia_dni_no_numerico():
    resultado = registrar_asistencia({"dni": "40A23456", "materia": "Programación III"})
    assert resultado is False

# Test 5: Rechazo si el campo DNI no existe, está vacío o no es un string
def test_registrar_asistencia_dni_invalido_o_vacio():
    assert registrar_asistencia({"materia": "Programación III"}) is False
    assert registrar_asistencia({"dni": ""}) is False
    assert registrar_asistencia({"dni": 12345678}) is False

# Test 6: Verificación de estructura y tipos del reporte estadístico
def test_obtener_reporte_estadistico():
    reporte = obtener_reporte_estadistico()
    assert "total_asistencias" in reporte
    assert "detalle" in reporte
    assert isinstance(reporte["detalle"], list)
