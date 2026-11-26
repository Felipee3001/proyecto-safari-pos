from .models import Categoria, Producto, Mesa, Empleado, CuentaFiado

def seed_database_if_empty():
    # 1. Categorías
    cat_comida, _ = Categoria.objects.get_or_create(
        codigo='comidarapida',
        defaults={'nombre': 'Comida Rápida', 'icono': '🍔'}
    )
    cat_bebidas, _ = Categoria.objects.get_or_create(
        codigo='bebestibles',
        defaults={'nombre': 'Bebestibles', 'icono': '🥤'}
    )
    cat_souvenirs, _ = Categoria.objects.get_or_create(
        codigo='souvenirs',
        defaults={'nombre': 'Souvenirs', 'icono': '🦁'}
    )

    # 2. Productos (12 por categoría = 36 productos temáticos Parque Safari)
    productos_defecto = [
        # 🍔 COMIDA RÁPIDA (12)
        ('Hamburguesa Safari + Papas', 6500, cat_comida, 'COCINA'),
        ('Completo Italiano XL + Papas', 3800, cat_comida, 'COCINA'),
        ('Papas Fritas Balde Familiar', 5000, cat_comida, 'COCINA'),
        ('Nuggets de Pollo Safari x10', 4200, cat_comida, 'COCINA'),
        ('Sándwich Mechada XL', 7200, cat_comida, 'COCINA'),
        ('Combo Rugido Doble + Papas + Bebida', 8900, cat_comida, 'COCINA'),
        ('Choripán del Explorador en Marraqueta', 3500, cat_comida, 'COCINA'),
        ('Empanada de Pino Horno de Barro', 2800, cat_comida, 'COCINA'),
        ('Hot Dog Jirafa Extra Largo', 4500, cat_comida, 'COCINA'),
        ('Cajita Infantil Cachorro Safari', 5200, cat_comida, 'COCINA'),
        ('Churrasco Italiano León', 6800, cat_comida, 'COCINA'),
        ('Fajita Pollo Crispy Safari', 5800, cat_comida, 'COCINA'),

        # 🥤 BEBESTIBLES (12)
        ('Néctar de Fruta Safari 500ml', 1800, cat_bebidas, 'BARRA'),
        ('Bebida de Fantasía Lata', 1500, cat_bebidas, 'BARRA'),
        ('Agua Mineral Premium', 1200, cat_bebidas, 'BARRA'),
        ('Jugo Natural Rugido de Naranja', 2500, cat_bebidas, 'BARRA'),
        ('Granizado Tropical Selva 500ml', 2800, cat_bebidas, 'BARRA'),
        ('Café de Grano Explorador', 2200, cat_bebidas, 'BARRA'),
        ('Helado Paleta Huella de Tigre', 2000, cat_bebidas, 'BARRA'),
        ('Mote con Huesillo Tradicional Safari', 2600, cat_bebidas, 'BARRA'),
        ('Limonada Menta Jengibre Sabana', 3000, cat_bebidas, 'BARRA'),
        ('Milkshake Vainilla Sabana', 3500, cat_bebidas, 'BARRA'),
        ('Té Helado Durazno Oasis', 2100, cat_bebidas, 'BARRA'),
        ('Chocolate Caliente Refugio', 2400, cat_bebidas, 'BARRA'),

        # 🧸 SOUVENIRS (12)
        ('Llavero Peluche León Safari', 4500, cat_souvenirs, 'BARRA'),
        ('Gorra Bordada Parque Safari', 7500, cat_souvenirs, 'BARRA'),
        ('Polera Oficial Huella Tigre', 12000, cat_souvenirs, 'BARRA'),
        ('Tazón Cerámica Cachorro León', 5500, cat_souvenirs, 'BARRA'),
        ('Binoculares de Explorador Infantil', 6500, cat_souvenirs, 'BARRA'),
        ('Sombrero Safari Ala Ancha', 8500, cat_souvenirs, 'BARRA'),
        ('Peluche Elefante Africano Mediano', 9900, cat_souvenirs, 'BARRA'),
        ('Imán Coleccionable Felinos Safari', 2500, cat_souvenirs, 'BARRA'),
        ('Cantimplora Térmica Expedición', 7000, cat_souvenirs, 'BARRA'),
        ('Peluche Jirafa Cuello Largo', 10500, cat_souvenirs, 'BARRA'),
        ('Mochila Explorador Junior', 13500, cat_souvenirs, 'BARRA'),
        ('Lápiz Conmemorativo León Safari', 1800, cat_souvenirs, 'BARRA'),
    ]

    for nom, pre, cat, elab in productos_defecto:
        Producto.objects.get_or_create(
            nombre=nom,
            defaults={
                'precio': pre,
                'categoria': cat,
                'tipo_elaboracion': elab,
                'activo': True
            }
        )

    # 3. Mesas (A1 a Z24)
    if Mesa.objects.count() == 0:
        mesas_crear = []
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            for num in range(1, 25):
                mesas_crear.append(Mesa(numero=f"{letra}{num}", seccion=letra, estado='DISPONIBLE'))
        Mesa.objects.bulk_create(mesas_crear)

    # 4. Empleados
    if Empleado.objects.count() == 0:
        emp_admin = Empleado.objects.create(
            nombre='Administrador General',
            user='admin.safari',
            pass_plain='admin2026',
            rol='Administrador',
            activo=True
        )
        emp_cajero = Empleado.objects.create(
            nombre='Operador Ventas 01',
            user='cajero.safari',
            pass_plain='caja2026',
            rol='Cajero',
            activo=True
        )
        emp_cocina = Empleado.objects.create(
            nombre='Chef Ejecutivo Safari',
            user='cocina.safari',
            pass_plain='chef2026',
            rol='Cocinero',
            activo=True
        )
        emp_mesero = Empleado.objects.create(
            nombre='Garzón Express Safari',
            user='mesero.safari',
            pass_plain='garzon2026',
            rol='Mesero',
            activo=True
        )

        # 5. Cuentas Fiado
        CuentaFiado.objects.create(
            empleado=emp_cajero,
            deuda=12500,
            ultimo_consumo='04/10/2026 12:30'
        )
        CuentaFiado.objects.create(
            empleado=emp_cocina,
            deuda=8400,
            ultimo_consumo='04/10/2026 14:15'
        )
