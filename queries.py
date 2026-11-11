QUERIES = {
    # 1. Inventario Bajo
    "1": """
        SELECT id_producto, nombre, categoria, stock, 
               ROUND((SELECT AVG(stock) FROM productos), 2) AS stock_promedio
        FROM productos
        WHERE stock < (SELECT AVG(stock) FROM productos)
        ORDER BY stock ASC;
    """,
    # 2. Ventas por Método de Pago
    "2": """
        SELECT metodo_pago, COUNT(id_venta) AS total_transacciones
        FROM ventas 
        GROUP BY metodo_pago 
        ORDER BY total_transacciones DESC;
    """,
    # 3. [INNER JOIN 1] Facturación por Cliente
    "3": """
        SELECT c.id_cliente, c.nombre, c.email, 
               COALESCE(SUM(dv.cantidad * dv.precio_unitario), 0) AS total_historico
        FROM clientes c
        INNER JOIN ventas v ON c.id_cliente = v.id_cliente
        INNER JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
        GROUP BY c.id_cliente, c.nombre, c.email 
        ORDER BY total_historico DESC;
    """,
    # 4. [INNER JOIN 2] Ventas por Sucursal
    "4": """
        SELECT s.id_sucursal, s.nombre, s.ciudad, SUM(dv.cantidad) AS total_unidades
        FROM sucursales s
        INNER JOIN ventas v ON s.id_sucursal = v.id_sucursal
        INNER JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
        GROUP BY s.id_sucursal, s.nombre, s.ciudad 
        ORDER BY total_unidades DESC;
    """,
    # 5. [INNER JOIN 3] Empleados y sus Sucursales
    "5": """
        SELECT e.id_empleado, e.nombre, e.departamento, e.salario, s.nombre AS sucursal
        FROM empleados e
        INNER JOIN sucursales s ON e.id_sucursal = s.id_sucursal
        ORDER BY s.nombre, e.salario DESC;
    """,
    # 6. [INNER JOIN 4] Detalle de Transacciones Recientes
    "6": """
        SELECT v.id_venta, v.fecha_venta, p.nombre AS producto, dv.cantidad, dv.precio_unitario,
               (dv.cantidad * dv.precio_unitario) AS subtotal
        FROM ventas v
        INNER JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
        INNER JOIN productos p ON dv.id_producto = p.id_producto
        ORDER BY v.fecha_venta DESC 
        LIMIT 10;
    """,
    # 7. Ranking de Empleados (Window Functions)
    "7": """
        SELECT id_empleado, nombre, departamento, salario,
               DENSE_RANK() OVER (PARTITION BY departamento ORDER BY salario DESC) AS ranking
        FROM empleados 
        ORDER BY departamento, ranking;
    """,
    # 8. Clientes con Compra Cruzada (Subconsultas Correlacionadas)
    "8": """
        SELECT c.id_cliente, c.nombre, c.email
        FROM clientes c
        WHERE EXISTS (
            SELECT 1 FROM ventas v
            JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
            JOIN productos p ON dv.id_producto = p.id_producto
            WHERE v.id_cliente = c.id_cliente AND p.categoria = 'Cosmética'
        ) AND NOT EXISTS (
            SELECT 1 FROM ventas v
            JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
            JOIN productos p ON dv.id_producto = p.id_producto
            WHERE v.id_cliente = c.id_cliente AND p.categoria = 'Alimentos'
        );
    """,
    # 9. Auditoría Mensual de Crecimiento (CTE + LAG)
    "9": """
        WITH VentasMensuales AS (
            SELECT DATE_TRUNC('month', v.fecha_venta) AS mes,
                   SUM(dv.cantidad * dv.precio_unitario) AS total_mes
            FROM ventas v
            JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
            GROUP BY DATE_TRUNC('month', v.fecha_venta)
        ),
        Crecimiento AS (
            SELECT TO_CHAR(mes, 'YYYY-MM') AS periodo, total_mes,
                   LAG(total_mes, 1) OVER (ORDER BY mes) AS mes_anterior
            FROM VentasMensuales
        )
        SELECT periodo, total_mes, mes_anterior,
               ROUND(CASE WHEN mes_anterior IS NULL THEN 0 ELSE ((total_mes - mes_anterior) / mes_anterior) * 100 END, 2) AS pct_crecimiento
        FROM Crecimiento;
    """,
    # 10. Súper Compradores (HAVING con agregación)
    "10": """
        SELECT c.id_cliente, c.nombre, SUM(dv.cantidad * dv.precio_unitario) AS gasto_acumulado
        FROM clientes c
        JOIN ventas v ON c.id_cliente = v.id_cliente
        JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
        GROUP BY c.id_cliente, c.nombre
        HAVING SUM(dv.cantidad * dv.precio_unitario) > (
            SELECT AVG(total) FROM (
                SELECT SUM(dv2.cantidad * dv2.precio_unitario) AS total
                FROM ventas v2 
                JOIN detalle_ventas dv2 ON v2.id_venta = dv2.id_venta 
                GROUP BY v2.id_cliente
            ) sub
        ) 
        ORDER BY gasto_acumulado DESC;
    """
}