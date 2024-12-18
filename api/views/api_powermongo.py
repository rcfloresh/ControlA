from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.conf import settings
from django.db import connection


def convert_to_str(data):
    """Convierte todos los valores en un diccionario o lista a cadenas."""
    if isinstance(data, dict):
        return {k: convert_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_str(item) for item in data]
    else:
        return str(data)


@csrf_exempt
def get_mongo_data(request):
    api_key = request.GET.get('api_key')

    # Verificar la API Key
    if api_key != settings.API_KEY:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        # Conectar a MongoDB
        client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'],
                             settings.DATABASES['mongodb']['CLIENT']['port'])
        db = client[settings.DATABASES['mongodb']['NAME']]
        collection = db['mdb_asistencia']

        # Obtener datos de MongoDB y convertir todos los campos a cadenas
        mongo_data = list(collection.find({}, {'_id': 0}))
        mongo_data = convert_to_str(mongo_data)

        # Conectar a MySQL y obtener datos de todas las tablas
        mysql_data = {}
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")  # Obtener todas las tablas de la base de datos
            tables = cursor.fetchall()

            # Iterar sobre todas las tablas y obtener sus datos
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                table_data = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
                mysql_data[table_name] = convert_to_str(table_data)

        # Fusionar datos de ambas bases de datos en la respuesta
        data = {
            'mongo_data': mongo_data,
            'mysql_data': mysql_data
        }

        return JsonResponse({'data': data}, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)