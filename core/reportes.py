import time
from decimal import Decimal

from django.db import connection


CONSULTAS = [
    {
        'clave': 'ingresos-por-categoria',
        'numero': 1,
        'titulo': 'Ingresos por categoría',
        'tecnica': 'SUM() + GROUP BY',
        'descripcion': 'Cuánto dinero ha generado cada categoría sumando todos los renglones de tus facturas.',
        'sql': """
SELECT c.nombre AS categoria,
       SUM(d.cantidad) AS unidades_vendidas,
       SUM(d.cantidad * d.precio_unitario) AS ingresos
FROM core_detallefactura AS d
JOIN core_factura AS f ON f.id = d.factura_id
JOIN core_servicio AS s ON s.id = d.servicio_id
JOIN core_categoria AS c ON c.id = s.categoria_id
WHERE f.usuario_id = %(uid)s
GROUP BY c.id, c.nombre
ORDER BY ingresos DESC
""",
    },
    {
        'clave': 'servicios-por-categoria',
        'numero': 2,
        'titulo': 'Servicios por categoría',
        'tecnica': 'COUNT() + GROUP BY + LEFT JOIN',
        'descripcion': 'Cuántos servicios tienes en cada categoría, incluidas las categorías que todavía no usas (salen con 0).',
        'sql': """
SELECT c.nombre AS categoria,
       COUNT(s.id) AS servicios
FROM core_categoria AS c
LEFT JOIN core_servicio AS s
       ON s.categoria_id = c.id
      AND s.propietario_id = %(uid)s
GROUP BY c.id, c.nombre
ORDER BY servicios DESC, c.nombre
""",
    },
    {
        'clave': 'precio-minimo-y-maximo',
        'numero': 3,
        'titulo': 'Servicio más barato y más caro (con empates)',
        'tecnica': 'MIN() + MAX() en una subconsulta',
        'descripcion': 'Muestra todos los servicios que tienen el precio mínimo y todos los que tienen el máximo, incluidos los empates.',
        'sql': """
SELECT CASE
           WHEN s.precio = m.minimo THEN 'Más barato (MIN)'
           ELSE 'Más caro (MAX)'
       END AS posicion,
       s.titulo AS servicio,
       c.nombre AS categoria,
       s.precio
FROM core_servicio AS s
JOIN (
    SELECT MIN(precio) AS minimo, MAX(precio) AS maximo
    FROM core_servicio
    WHERE propietario_id = %(uid)s
) AS m
  ON s.precio IN (m.minimo, m.maximo)
LEFT JOIN core_categoria AS c ON c.id = s.categoria_id
WHERE s.propietario_id = %(uid)s
ORDER BY s.precio, s.titulo
""",
    },
    {
        'clave': 'servicios-sin-vender',
        'numero': 4,
        'titulo': 'Servicios que nunca se han facturado',
        'tecnica': 'LEFT JOIN + IS NULL (anti-join)',
        'descripcion': 'Los servicios que todavía no aparecen en ninguna factura.',
        'sql': """
SELECT s.titulo AS servicio,
       c.nombre AS categoria,
       s.precio
FROM core_servicio AS s
LEFT JOIN core_detallefactura AS d ON d.servicio_id = s.id
LEFT JOIN core_categoria AS c ON c.id = s.categoria_id
WHERE s.propietario_id = %(uid)s
  AND d.id IS NULL
ORDER BY s.precio DESC
""",
    },
    {
        'clave': 'clientes-sobre-el-promedio',
        'numero': 5,
        'titulo': 'Clientes que gastan más que el promedio',
        'tecnica': 'HAVING + subconsulta con AVG()',
        'descripcion': 'Tus clientes que han comprado en total más que el promedio de todos tus clientes.',
        'sql': """
SELECT f.cliente,
       COUNT(DISTINCT f.id) AS facturas,
       SUM(d.cantidad * d.precio_unitario) AS total_comprado
FROM core_factura AS f
JOIN core_detallefactura AS d ON d.factura_id = f.id
WHERE f.usuario_id = %(uid)s
GROUP BY f.cliente
HAVING SUM(d.cantidad * d.precio_unitario) > (
    SELECT AVG(t.total_cliente)
    FROM (
        SELECT SUM(d2.cantidad * d2.precio_unitario) AS total_cliente
        FROM core_factura AS f2
        JOIN core_detallefactura AS d2 ON d2.factura_id = f2.id
        WHERE f2.usuario_id = %(uid)s
        GROUP BY f2.cliente
    ) AS t
)
ORDER BY total_comprado DESC
""",
    },
    {
        'clave': 'ranking-por-categoria',
        'numero': 6,
        'titulo': 'Ranking de servicios más vendidos por categoría',
        'tecnica': 'WITH (CTE) + RANK() OVER (PARTITION BY …)',
        'descripcion': 'El lugar de cada servicio en su categoría según las unidades vendidas; los empates comparten lugar.',
        'sql': """
WITH ventas AS (
    SELECT c.nombre AS categoria,
           s.titulo AS servicio,
           SUM(d.cantidad) AS unidades
    FROM core_detallefactura AS d
    JOIN core_factura AS f ON f.id = d.factura_id
    JOIN core_servicio AS s ON s.id = d.servicio_id
    JOIN core_categoria AS c ON c.id = s.categoria_id
    WHERE f.usuario_id = %(uid)s
    GROUP BY c.nombre, s.id, s.titulo
)
SELECT categoria,
       RANK() OVER (PARTITION BY categoria ORDER BY unidades DESC) AS lugar,
       servicio,
       unidades
FROM ventas
ORDER BY categoria, lugar, servicio
""",
    },
]


def buscar(clave):
    for consulta in CONSULTAS:
        if consulta['clave'] == clave:
            return consulta
    return None


def ejecutar_sql(sql, parametros=None):
    inicio = time.perf_counter()

    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        columnas = [columna[0] for columna in cursor.description]
        filas = cursor.fetchall()

    milisegundos = (time.perf_counter() - inicio) * 1000
    return columnas, filas, milisegundos


def formatear(valor):
    if valor is None:
        return {'texto': '—', 'numero': False}

    if isinstance(valor, bool):
        return {'texto': 'Sí' if valor else 'No', 'numero': False}

    if isinstance(valor, int):
        return {'texto': f'{valor:,}', 'numero': True}

    if isinstance(valor, (Decimal, float)):
        return {'texto': f'{valor:,.2f}', 'numero': True}

    return {'texto': str(valor), 'numero': False}