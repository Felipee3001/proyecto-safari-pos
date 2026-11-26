from django.db import models
from django.contrib.auth.models import User

class CajaSesion(models.Model):
    ESTADOS = [('ABIERTA', 'Abierta'), ('CERRADA', 'Cerrada')]
    
    cajero = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_apertura = models.IntegerField(default=0)  # Efectivo para sencillo/vueltos
    monto_cierre_sistema = models.IntegerField(default=0)  # Lo que calculó el sistema en ventas
    monto_cierre_real = models.IntegerField(default=0)  # Lo que el cajero contó físicamente
    estado = models.CharField(max_length=10, choices=ESTADOS, default='ABIERTA')

    def __str__(self):
        return f"Sesión {self.id} - {self.cajero.username} ({self.estado})"

class CuadraturaDetalle(models.Model):
    sesion = models.OneToOneField(CajaSesion, on_delete=models.CASCADE, related_name='cuadratura')
    # Billetes
    b_20000 = models.IntegerField(default=0)
    b_10000 = models.IntegerField(default=0)
    b_5000 = models.IntegerField(default=0)
    b_1000 = models.IntegerField(default=0)
    # Monedas
    m_500 = models.IntegerField(default=0)
    m_100 = models.IntegerField(default=0)
    m_50 = models.IntegerField(default=0)
    m_5 = models.IntegerField(default=0)
    m_1 = models.IntegerField(default=0)

class Categoria(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    TIPO_ELABORACION_CHOICES = [
        ('COCINA', 'Cocina'),
        ('BARRA', 'Barra'),
    ]
    nombre = models.CharField(max_length=150)
    precio = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    tipo_elaboracion = models.CharField(max_length=20, choices=TIPO_ELABORACION_CHOICES, default='COCINA')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('OCUPADA', 'Ocupada'),
    ]
    numero = models.CharField(max_length=20, unique=True)
    seccion = models.CharField(max_length=10, default='A')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')

    def __str__(self):
        return f"Mesa {self.numero} ({self.estado})"

class Empleado(models.Model):
    ROL_CHOICES = [
        ('Administrador', 'Administrador'),
        ('Cajero', 'Cajero'),
        ('Cocinero', 'Cocinero'),
        ('Mesero', 'Mesero'),
    ]
    nombre = models.CharField(max_length=150)
    user = models.CharField(max_length=100, unique=True)
    pass_plain = models.CharField(max_length=100)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)
    activo = models.BooleanField(default=True)
    mostrar_en_login = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.rol}) - {self.user}"

class CuentaFiado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='fiados')
    deuda = models.IntegerField(default=0)
    ultimo_consumo = models.CharField(max_length=100, default='')
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fiado {self.empleado.nombre}: ${self.deuda}"


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PREPARACION', 'En Preparación'),
        ('LISTO_ENTREGA', 'Listo para Entrega'),
        ('SERVIDO', 'Servido en Mesa'),
        ('ENTREGADO', 'Entregado / Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    MODALIDAD_CHOICES = [
        ('MESA', 'Mesa'),
        ('MESON', 'Mesón'),
    ]
    ESTADO_TICKET_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PREPARACION', 'En Preparación'),
        ('LISTO', 'Listo'),
        ('NO_APLICA', 'No Aplica'),
    ]
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta Débito/Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    numero_ticket = models.IntegerField(default=1)
    caja_sesion = models.ForeignKey(CajaSesion, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    tomado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_tomados')
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True)
    mesa_numero = models.CharField(max_length=20, default='')
    modalidad_entrega = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='MESA')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    estado_cocina = models.CharField(max_length=20, choices=ESTADO_TICKET_CHOICES, default='NO_APLICA')
    estado_barra = models.CharField(max_length=20, choices=ESTADO_TICKET_CHOICES, default='NO_APLICA')
    total = models.IntegerField(default=0)
    observaciones = models.TextField(blank=True, default='')
    creado_en = models.DateTimeField(auto_now_add=True)
    hora_str = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return f"Pedido #{self.numero_ticket} Mesa {self.mesa_numero} (${self.total})"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_producto = models.CharField(max_length=150)
    categoria = models.CharField(max_length=50, default='comidarapida')
    tipo_elaboracion = models.CharField(max_length=20, default='COCINA')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.IntegerField(default=0)
    subtotal = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.cantidad}x {self.nombre_producto} (Ticket #{self.pedido.numero_ticket})"

class SegmentacionTerminal(models.Model):
    terminal = models.CharField(max_length=30, unique=True)  # 'CAJA' o 'BARRA'
    categorias = models.CharField(max_length=255, default='comidarapida,bebestibles,souvenirs')
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Terminal {self.terminal}: {self.categorias}"
