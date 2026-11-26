from django.contrib import admin
from .models import Categoria, Producto, Mesa, Empleado, CuentaFiado, Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre')
    search_fields = ('nombre', 'codigo')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'categoria', 'tipo_elaboracion', 'activo')
    list_filter = ('categoria', 'tipo_elaboracion', 'activo')
    search_fields = ('nombre',)

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero', 'seccion', 'estado')
    list_filter = ('seccion', 'estado')
    search_fields = ('numero',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'user', 'rol', 'activo')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre', 'user')

@admin.register(CuentaFiado)
class CuentaFiadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'deuda', 'ultimo_consumo')
    list_filter = ('empleado__rol',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero_ticket', 'mesa_numero', 'modalidad_entrega', 'estado', 'estado_cocina', 'estado_barra', 'total', 'creado_en')
    list_filter = ('estado', 'modalidad_entrega', 'estado_cocina', 'estado_barra')
    search_fields = ('mesa_numero', 'numero_ticket')
    inlines = [DetallePedidoInline]
