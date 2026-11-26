from django.contrib import admin
from django.urls import path
from Safari import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('ventas/', views.ventas_view, name='ventas'),
    path('mesero/', views.mesero_view, name='mesero_panel'),
    path('mesas/', views.mesas_view, name='mesas'),
    path('kds/', views.kds_view, name='kds'),
    path('admin-panel/', views.admin_view, name='admin_panel'),

    # APIs Operativas (POS / KDS / Mesero)
    path('api/estado-general/', views.api_estado_general, name='api_estado_general'),
    path('api/mesa/toggle/', views.toggle_mesa_view, name='api_toggle_mesa'),
    path('api/pedido/guardar/', views.guardar_pedido_view, name='api_guardar_pedido'),
    path('api/kds/despachar/', views.api_kds_despachar, name='api_kds_despachar'),
    path('api/mesero/entregar/', views.api_mesero_entregar, name='api_mesero_entregar'),
    path('api/pedido/cambiar-estado/<int:pedido_id>/', views.cambiar_estado_pedido_view, name='api_cambiar_estado_pedido'),

    # APIs Panel Administrador (CRUD en Base de Datos)
    path('api/admin-datos/', views.api_admin_datos, name='api_admin_datos'),
    path('api/empleados/', views.api_empleados_crud, name='api_empleados_crud'),
    path('api/productos/', views.api_productos_crud, name='api_productos_crud'),
    path('api/mesas/', views.api_mesas_crud, name='api_mesas_crud'),
    path('api/fiados/', views.api_fiados_crud, name='api_fiados_crud'),

    path('api/caja/abrir/', views.abrir_caja_api, name='abrir_caja_api'),
    path('api/caja/cerrar/', views.cerrar_caja_api, name='cerrar_caja_api'),
    path('api/caja/verificar-estado/', views.verificar_estado_caja_api, name='api_verificar_caja'),

    path('api/caja/pausar/', views.pausar_caja_api, name='pausar_caja_api'),
    path('api/segmentacion/', views.api_segmentacion_terminal, name='api_segmentacion_terminal'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
