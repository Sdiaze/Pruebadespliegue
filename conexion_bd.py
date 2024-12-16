# conexion_bd.py

import pyodbc
import hashlib
import dash_bootstrap_components as dbc
import os


# Función para conectar a la base de datos
def conectar_bd():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={os.getenv("SQL_SERVER")};'
            f'DATABASE={os.getenv("SQL_DATABASE")};'
            f'UID={os.getenv("SQL_USER")};'
            f'PWD={os.getenv("SQL_PASSWORD")};'
            'Encrypt=yes;'
            'TrustServerCertificate=no;'
        )
        return conn
    except pyodbc.Error as e:
        raise ConnectionError(f"Error al conectar a la base de datos: {e}")



def crear_usuario(username, password):
    """
    Crea un nuevo usuario con credenciales encriptadas.
    Retorna True si el usuario fue creado exitosamente, False en caso de error.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO Usuarios (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        return True
    except pyodbc.IntegrityError:
        # Esto ocurre si el usuario ya existe
        return False
    except pyodbc.Error as e:
        # Manejo de errores generales
        print(f"Error al crear usuario: {e}")
        return False
    finally:
        conn.close()



def verificar_credenciales(username, password):
    """
    Verifica las credenciales de un usuario.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute(
            "SELECT * FROM Usuarios WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        usuario = cursor.fetchone()
        return usuario is not None
    finally:
        conn.close()


# Funciones relacionadas con ubicaciones y pallets
def asignar_ubicacion(pallet_id, tipo_almacen, piso, rack, letra):
    """
    Asigna una ubicación a un pallet en el almacén.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        # Validar que el pallet ID sea un entero
        pallet_id = int(pallet_id)

        # Verificar si el pallet existe
        cursor.execute("SELECT 1 FROM pallets WHERE id_pallet = ?", (pallet_id,))
        if cursor.fetchone() is None:
            return f"Error: El Pallet con ID {pallet_id} no existe."

        # Verificar si el pallet ya tiene una ubicación asignada
        cursor.execute(
            "SELECT ubicacion_key FROM ubicaciones WHERE id_pallet_asignado = ?",
            (pallet_id,)
        )
        ubicacion_actual = cursor.fetchone()
        if ubicacion_actual:
            return f"Error: El Pallet ya tiene una ubicación asignada: {ubicacion_actual[0]}."

        # Asignar ubicación mediante procedimientos almacenados
        cursor.execute(
            "EXEC reasignar_pallet @piso=?, @rack=?, @letra=?, @id_pallet=?",
            (piso, rack, letra, pallet_id)
        )
        conn.commit()

        cursor.execute("EXEC actualizar_status_ubicacion")
        conn.commit()

        return f"Pallet {pallet_id} asignado a la ubicación {tipo_almacen}, {piso}, {rack}, {letra}."
    except ValueError:
        return "Error: El ID del pallet debe ser un número entero."
    except pyodbc.Error as e:
        return f"Error al asignar ubicación: {e}"
    finally:
        conn.close()


def liberar_ubicacion(pallet_id):
    """
    Libera una ubicación ocupada por un pallet y reorganiza posiciones.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        # Validar que el pallet ID sea un entero
        pallet_id = int(pallet_id)

        # Verificar si el pallet existe
        cursor.execute("SELECT 1 FROM pallets WHERE id_pallet = ?", (pallet_id,))
        if cursor.fetchone() is None:
            return f"Error: El Pallet con ID {pallet_id} no existe."

        # Verificar si el pallet tiene una ubicación asignada
        cursor.execute(
            "SELECT id_ubicacion, posicion_pallet FROM asignacion_pallet WHERE id_pallet = ?",
            (pallet_id,)
        )
        result = cursor.fetchone()
        if result is None:
            return f"Error: El Pallet con ID {pallet_id} no está asignado a ninguna ubicación."

        id_ubicacion, posicion_actual = result

        # Verificar si el pallet está en la posición 1
        if posicion_actual != 1:
            return "Error: Solo se puede retirar el pallet de la posición 1."

        # Retirar el pallet
        cursor.execute("EXEC retirar_pallet @id_pallet = ?", (pallet_id,))
        conn.commit()

        cursor.execute("EXEC actualizar_status_ubicacion")
        conn.commit()

        return f"Ubicación liberada y reorganizada para el Pallet {pallet_id}."
    except ValueError:
        return "Error: El ID del pallet debe ser un número entero."
    except pyodbc.Error as e:
        conn.rollback()
        return f"Error al liberar ubicación: {e}"
    finally:
        conn.close()


def obtener_todas_las_posiciones():
    """
    Recupera todas las posiciones del almacén, incluyendo id_pallet_asignado, descripción, variedad, mercado, fecha de faena y NPallet.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                u.tipo_almacen, 
                u.piso, 
                u.rack, 
                u.letra, 
                u.posicion_pallet, 
                u.status_ubicacion, 
                u.id_pallet_asignado,
                p.descripcion,
                p.Variedad,
                p.Mercado,
                p.fechafaena,
                p.NPallet
            FROM ubicaciones u
            LEFT JOIN pallets p ON u.id_pallet_asignado = p.id_pallet
        """)
        return cursor.fetchall()
    finally:
        conn.close()




def obtener_opciones_campo():
    """
    Recupera las opciones únicas de cada campo desde la base de datos.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT DISTINCT tipo_almacen FROM ubicaciones")
        tipos_almacen = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT piso FROM ubicaciones")
        pisos = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT rack FROM ubicaciones")
        racks = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT letra FROM ubicaciones")
        letras = [row[0] for row in cursor.fetchall()]

        return tipos_almacen, pisos, racks, letras
    finally:
        conn.close()


def obtener_opciones_disponibles(tipo_almacen=None, piso=None, rack=None, letra=None):
    """
    Recupera las opciones disponibles basadas en los filtros seleccionados.
    """
    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        query = """
            SELECT DISTINCT tipo_almacen, piso, rack, letra
            FROM ubicaciones
            WHERE status_ubicacion = 'Libre'
        """
        conditions = []
        params = []

        if tipo_almacen:
            conditions.append("tipo_almacen = ?")
            params.append(tipo_almacen)
        if piso:
            conditions.append("piso = ?")
            params.append(piso)
        if rack:
            conditions.append("rack = ?")
            params.append(rack)
        if letra:
            conditions.append("letra = ?")
            params.append(letra)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY tipo_almacen, piso, rack, letra"

        cursor.execute(query, params)
        opciones_libres = cursor.fetchall()

        # Organizar los datos
        tipos_almacen = sorted(set(row[0] for row in opciones_libres))
        pisos = sorted(set(row[1] for row in opciones_libres if row[1]))
        racks = sorted(set(row[2] for row in opciones_libres if row[2]))
        letras = sorted(set(row[3] for row in opciones_libres if row[3]))

        return tipos_almacen, pisos, racks, letras
    finally:
        conn.close()



def ingresar_pallet(qr_data):
    """
    Inserta un pallet en la base de datos utilizando el procedimiento almacenado InsertPalletFromQR.

    Args:
        qr_data (str): Los datos del código QR que se deben insertar en la base de datos.

    Returns:
        str: Un mensaje indicando si el ingreso fue exitoso o si hubo un error.
    """
    if qr_data:
        # Dividir los datos del QR
        datos = qr_data.split(',')
        
        if len(datos) != 5:
            return dbc.Alert(f"Error: El formato del QR no es válido. Debe tener 5 campos separados por comas.", color="danger")
        
        # Extraer cada campo
        variedad = datos[0]
        descripcion = datos[1]
        mercado = datos[2]
        fecha_faena = datos[3]
        n_pallet = datos[4]
        
        # Verificar la longitud de FechaFaena
        if len(fecha_faena) != 8 or not fecha_faena.isdigit():
            return dbc.Alert(f"Error: La Fecha Faena debe tener exactamente 8 caracteres numéricos. Valor proporcionado: {fecha_faena}", color="danger")

        # Verificar la longitud de NPallet
        if len(n_pallet) != 8:
            return dbc.Alert(f"Error: El NPallet debe tener exactamente 8 caracteres. Valor proporcionado: {n_pallet}", color="danger")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            # Verificar si el NPallet ya existe
            cursor.execute("SELECT COUNT(*) FROM pallets WHERE NPallet = ?", (n_pallet,))
            if cursor.fetchone()[0] > 0:
                return dbc.Alert(f"Error: El NPallet '{n_pallet}' ya existe en la base de datos.", color="danger")
            
            # Ejecutar el procedimiento almacenado para insertar el pallet desde el QR
            cursor.execute("EXEC InsertPalletFromQR @qrData = ?", (qr_data,))
            conn.commit()
            return dbc.Alert(f"Pallet ingresado exitosamente con datos: {qr_data}", color="success")
        except pyodbc.Error as e:
            return dbc.Alert(f"Error al ingresar pallet: {e}", color="danger")
        finally:
            conn.close()
    return ""



# Función para cerrar la conexión a la base de datos
def cerrar_conexion_bd(conn):
    """
    Cierra una conexión a la base de datos.
    Si conn es None, no realiza ninguna acción.
    """
    try:
        if conn is not None:
            conn.close()
            print("Conexión a la base de datos cerrada correctamente.")
    except Exception as e:
        print(f"Error al cerrar la conexión a la base de datos: {e}")