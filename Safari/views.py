import json
import re
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Q
from .models import Categoria, Producto, Mesa, Empleado, CuentaFiado, Pedido, DetallePedido, CajaSesion, CuadraturaDetalle
from .seeder import seed_database_if_empty

# ========================================================
# 🔑 CONTROL DE ACCESO (LOGIN)
# ========================================================
@csrf_exempt
def login_view(request):
    from django.contrib.auth import logout as django_logout
    from django.contrib.auth.models import User
    from .models import Empleado

    def obtener_contexto_login(mensaje_error=None):
        contexto = {
            'empleados_login': list(
                Empleado.objects.filter(mostrar_en_login=True).order_by('id')
            )
        }
        if mensaje_error:
            contexto['error'] = mensaje_error
        return contexto
    # 1. REPARADOR AUTOMÁTICO DE USUARIOS (Solo crea si NO existen y protege al Admin)
    if request.method == 'GET':
        usuarios_maestros = [
            ('admin.safari', 'admin2026', 'Administrador', 'Administrador General'),
            ('cajero.safari', 'caja2026', 'Cajero', 'Cajero Operativo 1'),
            ('cocina.safari', 'chef2026', 'Cocinero', 'Jefe de Cocina'),
            ('mesero.safari', 'garzon2026', 'Mesero', 'Mesero Safari 1')
        ]
        for username, password, rol, nombre in usuarios_maestros:
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
                user_obj = User.objects.create_user(
                    username=username,
                    password=password
                )
            empleado_obj = Empleado.objects.filter(user=username).first()
            if not empleado_obj:
                Empleado.objects.create(
                    nombre=nombre,
                    user=username,
                    pass_plain=password,
                    rol=rol,
                    activo=True,
                    mostrar_en_login=True
                )
            elif rol == 'Administrador':
                if not user_obj.is_active:
                    user_obj.is_active = True
                    user_obj.save()
                if not empleado_obj.activo:
                    empleado_obj.activo = True
                    empleado_obj.save()
    # 2. PROCESAMIENTO DEL LOGIN
    if request.method == 'POST':
        user_input = request.POST.get('username', '').strip().lower()
        pass_input = request.POST.get('password', '').strip()
        if not re.fullmatch(r'[a-z0-9._-]{1,100}', user_input):
            return render(
                request,
                'login.html',
                obtener_contexto_login(
                    '❌ Usuario inválido. Solo se permiten letras, números, punto, guion y guion bajo.'
                ),
                status=400
            )
        if request.user.is_authenticated:
            django_logout(request)
            request.session.flush()
        empleado = Empleado.objects.filter(user__iexact=user_input).first()
        if empleado:
            rol_verificado = str(empleado.rol).strip()
            if rol_verificado != 'Administrador' and not empleado.activo:
                return render(
                    request,
                    'login.html',
                    obtener_contexto_login(
                        '⛔ Tu cuenta está deshabilitada. Contacta al Administrador.'
                    )
                )
        user = authenticate(
            request,
            username=user_input,
            password=pass_input
        )
        if user is not None:
            if empleado:
                rol_usuario = str(empleado.rol).strip()
            else:
                if 'admin' in user_input:
                    rol_usuario = 'Administrador'
                elif 'cajero' in user_input:
                    rol_usuario = 'Cajero'
                elif 'cocina' in user_input or 'chef' in user_input:
                    rol_usuario = 'Cocinero'
                else:
                    rol_usuario = 'Cajero'
            if rol_usuario != 'Administrador' and empleado and not empleado.activo:
                return render(
                    request,
                    'login.html',
                    obtener_contexto_login(
                        '⛔ Tu cuenta está deshabilitada. Contacta al Administrador.'
                    )
                )
            login(request, user)
            request.session['usuario_rol'] = rol_usuario

            if rol_usuario == 'Mesero':
                return redirect('mesero_panel')
            elif rol_usuario == 'Administrador':
                return redirect('admin_panel')
            elif rol_usuario in ['Cocinero', 'Cocina']:
                return redirect('kds')
            else:
                return redirect('ventas')
        else:
            return render(
                request,
                'login.html',
                obtener_contexto_login(
                    '❌ Usuario o Contraseña incorrectos.'
                )
            )
    return render(request, 'login.html', obtener_contexto_login())

@login_required
def mesero_view(request):
    """Renderiza la terminal móvil para los meseros."""
    rol = request.session.get('usuario_rol', '')

    if rol != 'Mesero':
        return redirect('ventas')

    return render(
        request,
        'mesero.html',
        {'usuario_rol_django': 'Mesero'}
    )
def logout_view(request):
    request.session.flush()
    return redirect('/')

# ========================================================
# 💸 2. VISTAS PRINCIPALES DE INTERFAZ OPERATIVA
# ========================================================
def ventas_view(request):
    productos = Producto.objects.filter(activo=True)
    mesas = Mesa.objects.all()
    pedidos_pendientes = Pedido.objects.filter(
        estado__in=['PENDIENTE', 'PREPARACION']
    )
    # Si visitas /ventas/ directamente, prioriza Cajero si la sesión fue pisada por otra pestaña
    rol_sesion = request.session.get('usuario_rol', 'Cajero')
    if request.path == '/ventas/' and rol_sesion in ['Cocinero', 'Cocina', 'Mesero']:
        rol_sesion = 'Cajero'
    return render(request, 'prototipo.html', {
        'productos': productos,
        'mesas': mesas,
        'pedidos': pedidos_pendientes,
        'usuario_rol_django': rol_sesion
    })

def kds_view(request):
    productos = Producto.objects.filter(activo=True)
    mesas = Mesa.objects.all()
    pedidos_pendientes = Pedido.objects.filter(
        estado__in=['PENDIENTE', 'PREPARACION']
    )
    # Al entrar a /kds/ muestra siempre la vista de Cocinero
    return render(request, 'prototipo.html', {
        'productos': productos,
        'mesas': mesas,
        'pedidos': pedidos_pendientes,
        'usuario_rol_django': 'Cocinero'
    })

def mesas_view(request):
    return ventas_view(request)

def admin_view(request):
    seed_database_if_empty()
    return render(request, 'admin.html')

# ========================================================
# 🔄 3. API: ESTADO GENERAL
# ========================================================
def api_estado_general(request):
    """Retorna productos, mesas sincronizadas, comandas KDS (Cocina 4 cols / Barra 2 cols) y mesero (2 cols)."""
    try:
        from django.db.models import Q
        from .models import SegmentacionTerminal

        mesas = list(
            Mesa.objects.all().values('id', 'numero')
        )

        productos_qs = Producto.objects.filter(
            activo=True
        ).select_related('categoria')

        # 🎯 FILTRO POR SEGMENTACIÓN DE USUARIO (Configurado en Admin)
        if request.user.is_authenticated:
            seg_usuario = SegmentacionTerminal.objects.filter(
                terminal=f"USER_{request.user.username}"
            ).first()
            if seg_usuario:
                cats_permitidas = [c.strip().lower() for c in seg_usuario.categorias.split(',') if c.strip()]
                productos_qs = productos_qs.filter(categoria__codigo__in=cats_permitidas)

        productos = []
        for p in productos_qs:
            cat_codigo = p.categoria.codigo if p.categoria else 'comidarapida'
            productos.append({
                'id': p.id,
                'name': p.nombre,
                'price': p.precio,
                'categoria': str(cat_codigo).strip().lower(),
                'tipo_elaboracion': p.tipo_elaboracion or 'COCINA'
            })

        # Sincronización real de mesas ocupadas
        mesas_con_pedidos_activos = set(
            Pedido.objects.filter(
                modalidad_entrega='MESA',
                estado__in=['PENDIENTE', 'PREPARACION', 'LISTO_ENTREGA', 'SERVIDO']
            ).exclude(
                mesa_numero__in=['', 'MESON', 'NONE']
            ).values_list('mesa_numero', flat=True)
        )

        Mesa.objects.filter(estado='OCUPADA').exclude(
            numero__in=mesas_con_pedidos_activos
        ).update(estado='DISPONIBLE')

        mesas_ocupadas = list(mesas_con_pedidos_activos)

        # 1. PEDIDOS EN PREPARACIÓN (COCINA Y BARRA) - Orden ascendente
        pedidos_activos_qs = Pedido.objects.filter(
            estado__in=['PENDIENTE', 'PREPARACION']
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_cocina = []
        pedidos_barra = []

        for ped in pedidos_activos_qs:
            items_cocina = []
            items_barra = []

            for d in ped.detalles.all():
                cat_det = str(d.categoria or '').strip().lower()
                item_data = {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip(),
                    'precio': int(d.precio_unitario or 0),
                    'subtotal': int(d.subtotal or 0)
                }

                # Solo souvenirs o pedidos de MESÓN van a Barra; todo lo de MESA va a Cocina
                if ped.modalidad_entrega == 'MESON' or cat_det == 'souvenirs':
                    items_barra.append(item_data)
                else:
                    items_cocina.append(item_data)

            if items_cocina and ped.estado_cocina != 'LISTO' and ped.modalidad_entrega == 'MESA':
                pedidos_cocina.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket,
                    'mesa': ped.mesa_numero if ped.mesa_numero else "Salón",
                    'hora': ped.hora_str or "18:00",
                    'estado': ped.estado_cocina or 'PENDIENTE',
                    'observaciones': ped.observaciones,
                    'items': items_cocina
                })

            if items_barra and ped.estado_barra != 'LISTO':
                pedidos_barra.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket,
                    'mesa': ped.mesa_numero if ped.modalidad_entrega == 'MESA' else "📦 MESÓN/CAJA",
                    'hora': ped.hora_str or "18:00",
                    'estado': ped.estado_barra or 'PENDIENTE',
                    'observaciones': ped.observaciones,
                    'items': items_barra
                })

        # 2. ENTREGADOS A MESERO (En camino a la mesa) - Orden ascendente
        pedidos_en_mesero_qs = Pedido.objects.filter(
            Q(estado='LISTO_ENTREGA') | Q(estado_cocina='LISTO', estado__in=['PENDIENTE', 'PREPARACION']),
            modalidad_entrega='MESA'
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_cocina_mesero = []
        for ped in pedidos_en_mesero_qs:
            items_coc = [
                {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if str(d.categoria or '').strip().lower() != 'souvenirs'
            ]
            if items_coc:
                pedidos_cocina_mesero.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket or ped.id,
                    'mesa': ped.mesa_numero or 'Salón',
                    'hora': ped.hora_str or '',
                    'observaciones': ped.observaciones,
                    'items': items_coc
                })
        # 3. SERVIDOS EN MESA (Mesa sigue ocupada en consumo) - Orden ascendente
        pedidos_servidos_qs = Pedido.objects.filter(
            estado='SERVIDO',
            modalidad_entrega='MESA'
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_cocina_servidos = []
        for ped in pedidos_servidos_qs:
            items_coc = [
                {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if str(d.categoria or '').strip().lower() != 'souvenirs'
            ]
            if items_coc:
                pedidos_cocina_servidos.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket or ped.id,
                    'mesa': ped.mesa_numero or 'Salón',
                    'hora': ped.hora_str or '',
                    'observaciones': ped.observaciones,
                    'items': items_coc
                })

        # 3B. PRODUCTOS YA ENTREGADOS Y FINALIZADOS EN COCINA (Mesa desocupada hoy) - Orden ascendente
        ahora_local = localtime(timezone.now())
        inicio_dia = ahora_local.replace(hour=0, minute=0, second=0, microsecond=0)

        pedidos_finalizados_qs = Pedido.objects.filter(
            estado='ENTREGADO',
            modalidad_entrega='MESA',
            creado_en__gte=inicio_dia
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_cocina_finalizados = []
        for ped in pedidos_finalizados_qs:
            items_coc = [
                {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if str(d.categoria or '').strip().lower() != 'souvenirs'
            ]
            if items_coc:
                pedidos_cocina_finalizados.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket or ped.id,
                    'mesa': ped.mesa_numero or 'Salón',
                    'hora': ped.hora_str or '',
                    'observaciones': ped.observaciones,
                    'items': items_coc
                })
        # 3C. BARRA / MESÓN / SOUVENIRS: PRODUCTOS FINALIZADOS HOY - Orden ascendente
        pedidos_barra_fin_qs = Pedido.objects.filter(
            estado_barra='LISTO',
            creado_en__gte=inicio_dia
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_barra_finalizados = []
        for ped in pedidos_barra_fin_qs:
            items_bar = [
                {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if ped.modalidad_entrega == 'MESON' or str(d.categoria or '').strip().lower() == 'souvenirs'
            ]
            if items_bar:
                pedidos_barra_finalizados.append({
                    'id': ped.id,
                    'numero_ticket': ped.numero_ticket or ped.id,
                    'mesa': ped.mesa_numero if ped.modalidad_entrega == 'MESA' else "📦 MESÓN/CAJA",
                    'hora': ped.hora_str or '',
                    'observaciones': ped.observaciones,
                    'items': items_bar
                })

        # 4. CATEGORÍA 1 MESERO: PEDIDOS LISTOS PARA RETIRAR - Orden ascendente
        pedidos_para_mesero_qs = Pedido.objects.filter(
            estado='LISTO_ENTREGA',
            modalidad_entrega='MESA'
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_cocina_terminada = Pedido.objects.filter(
            estado_cocina='LISTO',
            estado__in=['PENDIENTE', 'PREPARACION'],
            modalidad_entrega='MESA'
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_unicos = {
            p.id: p for p in (list(pedidos_para_mesero_qs) + list(pedidos_cocina_terminada))
        }

        pedidos_mesero = []
        for ped in sorted(pedidos_unicos.values(), key=lambda x: (x.numero_ticket or x.id, x.id)):
            items_para_llevar = [
                {
                    'text': str(d.nombre_producto or 'Producto').strip(),
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if str(d.categoria or '').strip().lower() != 'souvenirs'
            ]

            identificador_mesa = str(ped.mesa_numero or '').strip()
            if not identificador_mesa and ped.mesa:
                identificador_mesa = str(ped.mesa.numero).strip()

            if items_para_llevar:
                pedidos_mesero.append({
                    'id': int(ped.id),
                    'numero_ticket': int(ped.numero_ticket or ped.id or 1),
                    'mesa': identificador_mesa or 'Salón',
                    'hora': str(ped.hora_str or 'Ahora'),
                    'items': items_para_llevar
                })

        # 5. CATEGORÍA 2 MESERO: SERVIDOS EN MESA (ESPERANDO LIBERAR MESA) - Orden ascendente
        pedidos_consumo_qs = Pedido.objects.filter(
            estado='SERVIDO',
            modalidad_entrega='MESA'
        ).prefetch_related('detalles').order_by('numero_ticket', 'id')

        pedidos_mesero_consumo = []
        for ped in pedidos_consumo_qs:
            items_consumo = [
                {
                    'cantidad': int(d.cantidad or 1),
                    'nombre': str(d.nombre_producto or 'Producto').strip()
                }
                for d in ped.detalles.all()
                if str(d.categoria or '').strip().lower() != 'souvenirs'
            ]
            if items_consumo:
                pedidos_mesero_consumo.append({
                    'id': int(ped.id),
                    'numero_ticket': int(ped.numero_ticket or ped.id),
                    'mesa': str(ped.mesa_numero or 'Salón').strip(),
                    'hora': str(ped.hora_str or 'Ahora'),
                    'items': items_consumo
                })

        return JsonResponse({
            'status': 'success',
            'productos': productos,
            'mesas_ocupadas': mesas_ocupadas,
            'pedidos_cocina': pedidos_cocina,
            'pedidos_cocina_mesero': pedidos_cocina_mesero,
            'pedidos_cocina_servidos': pedidos_cocina_servidos,
            'pedidos_cocina_finalizados': pedidos_cocina_finalizados,
            'pedidos_barra': pedidos_barra,
            'pedidos_barra_finalizados': pedidos_barra_finalizados,
            'pedidos_mesero': pedidos_mesero,
            'pedidos_mesero_consumo': pedidos_mesero_consumo,
            'mesas': mesas
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
# ========================================================
# 📥 4. APIS OPERATIVAS DE CONTROL TRANSACCIONAL
# ========================================================
@csrf_exempt
def guardar_pedido_view(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        }, status=405)

    try:
        from django.db.models import Max

        data = json.loads(request.body)
        productos_carrito = data.get('productos', [])
        total_pedido = data.get('total', 0)

        numero_mesa = str(
            data.get('mesa_numero', '')
        ).strip().upper()

        observaciones_cliente = (
            data.get('observaciones', '').strip()
            or "Venta en Caja"
        )

        modalidad = data.get(
            'modalidad_entrega', 'MESA'
        ).strip().upper()

        if not productos_carrito:
            return JsonResponse({
                'status': 'error',
                'message': 'El carrito está vacío.'
            }, status=400)

        mesa_db = None

        if modalidad == 'MESA' and numero_mesa:
            mesa_db = Mesa.objects.filter(
                numero=numero_mesa
            ).first()

            if not mesa_db and numero_mesa.isdigit():
                mesa_db = Mesa.objects.filter(
                    numero__endswith=numero_mesa
                ).first()

            if mesa_db:
                mesa_db.estado = 'OCUPADA'
                mesa_db.save()
                numero_mesa = mesa_db.numero
            else:
                modalidad = 'MESON'
                numero_mesa = 'MESON'
        else:
            modalidad = 'MESON'
            numero_mesa = 'MESON'

        # Obtener el número de ticket más alto sin repetir aunque se borren pedidos
        ultimo_ticket = Pedido.objects.aggregate(Max('numero_ticket'))['numero_ticket__max'] or 0

        nuevo_pedido = Pedido.objects.create(
            numero_ticket=ultimo_ticket + 1,
            mesa=mesa_db,
            mesa_numero=numero_mesa,
            modalidad_entrega=modalidad,
            estado='PENDIENTE',
            estado_cocina='PENDIENTE',
            estado_barra='PENDIENTE',
            total=int(total_pedido),
            observaciones=observaciones_cliente,
            hora_str=localtime(
                timezone.now()
            ).strftime('%H:%M')
        )

        # Limpiar cualquier detalle huérfano asociado al ID recién creado
        DetallePedido.objects.filter(pedido=nuevo_pedido).delete()

        # Agrupar productos repetidos antes de guardar en DetallePedido
        productos_agrupados = {}
        for item in productos_carrito:
            nombre_buscar = ' '.join(str(item.get('name', '')).split()).strip()
            clave = nombre_buscar.lower()
            cantidad_real = int(item.get('cantidad', 1))
            precio_unitario_real = int(item.get('price', 0))

            if clave in productos_agrupados:
                productos_agrupados[clave]['cantidad'] += cantidad_real
            else:
                productos_agrupados[clave] = {
                    'name': nombre_buscar,
                    'price': precio_unitario_real,
                    'cantidad': cantidad_real,
                    'categoria': item.get('categoria', 'comidarapida')
                }

        for item in productos_agrupados.values():
            nombre_buscar = item['name']
            producto_db = Producto.objects.filter(nombre__iexact=nombre_buscar).first()

            precio_unitario_real = item['price']
            cantidad_real = item['cantidad']

            cat_codigo = (
                producto_db.categoria.codigo
                if (producto_db and producto_db.categoria)
                else str(item.get('categoria', 'comidarapida')).strip().lower()
            ).strip().lower()

            # Si es para MESA, todo va a COCINA excepto 'souvenirs'
            if modalidad == 'MESA':
                tipo_elab = 'BARRA' if cat_codigo == 'souvenirs' else 'COCINA'
            else:
                tipo_elab = 'BARRA'

            DetallePedido.objects.create(
                pedido=nuevo_pedido,
                producto=producto_db,
                nombre_producto=nombre_buscar,
                categoria=cat_codigo,
                tipo_elaboracion=tipo_elab,
                cantidad=cantidad_real,
                precio_unitario=precio_unitario_real,
                subtotal=precio_unitario_real * cantidad_real
            )

        # Ajustar estados iniciales según lo clasificado
        tiene_cocina = nuevo_pedido.detalles.filter(tipo_elaboracion='COCINA').exists()
        tiene_barra = nuevo_pedido.detalles.filter(tipo_elaboracion='BARRA').exists()

        nuevo_pedido.estado_cocina = 'PENDIENTE' if (tiene_cocina and modalidad == 'MESA') else 'NO_APLICA'
        nuevo_pedido.estado_barra = 'PENDIENTE' if (tiene_barra or modalidad == 'MESON') else 'NO_APLICA'
        nuevo_pedido.save()

        return JsonResponse({
            'status': 'success',
            'id_pedido': nuevo_pedido.id,
            'numero_ticket': nuevo_pedido.numero_ticket
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def api_kds_despachar(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        }, status=405)

    try:
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        tipo = data.get('tipo', 'COCINA').upper()
    except Exception:
        return JsonResponse({
            'status': 'error',
            'message': 'Datos inválidos.'
        }, status=400)

    pedido = Pedido.objects.filter(id=pedido_id).first()

    if not pedido:
        return JsonResponse({
            'status': 'error',
            'message': 'Pedido no encontrado.'
        }, status=404)

    if tipo == 'COCINA':
        pedido.estado_cocina = 'LISTO'
    elif tipo == 'BARRA':
        pedido.estado_barra = 'LISTO'

    tiene_barra = pedido.detalles.filter(categoria='souvenirs').exists() or pedido.modalidad_entrega == 'MESON'
    if not tiene_barra:
        pedido.estado_barra = 'NO_APLICA'

    tiene_cocina = pedido.detalles.exclude(categoria='souvenirs').exists() and pedido.modalidad_entrega == 'MESA'
    if not tiene_cocina:
        pedido.estado_cocina = 'NO_APLICA'

    # Verificar si ambas estaciones terminaron
    if (
        pedido.estado_cocina in ['LISTO', 'NO_APLICA']
        and pedido.estado_barra in ['LISTO', 'NO_APLICA']
    ):
        # Si es retiro en MESÓN o si SOLO tenía souvenirs (sin cocina)
        if pedido.modalidad_entrega == 'MESON' or not tiene_cocina:
            pedido.estado = 'ENTREGADO'
            pedido.save()

            # Liberar la mesa si no tiene otros pedidos activos
            if pedido.mesa_numero and pedido.mesa_numero != 'MESON':
                pedidos_activos_mesa = Pedido.objects.filter(
                    mesa_numero=pedido.mesa_numero,
                    estado__in=['PENDIENTE', 'PREPARACION', 'LISTO_ENTREGA', 'SERVIDO']
                ).exists()

                if not pedidos_activos_mesa:
                    mesa_obj = Mesa.objects.filter(numero=pedido.mesa_numero).first()
                    if mesa_obj:
                        mesa_obj.estado = 'DISPONIBLE'
                        mesa_obj.save()
        else:
            # Si tiene productos de cocina/bebestibles para mesa, pasa al Mesero
            pedido.estado = 'LISTO_ENTREGA'
            pedido.save()
    else:
        pedido.estado = 'PREPARACION'
        pedido.save()

    return JsonResponse({
        'status': 'success',
        'pedido_id': pedido.id,
        'estado': pedido.estado
    })

@csrf_exempt
def api_mesero_entregar(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        accion = data.get('accion', 'servir').strip().lower()
        nota_devolucion = data.get('nota_devolucion', '').strip()

        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado.'}, status=404)

        if accion == 'servir':
            pedido.estado = 'SERVIDO'
            pedido.save()
            mensaje_respuesta = f"Pedido #{pedido.numero_ticket} entregado en Mesa {pedido.mesa_numero}."

        elif accion == 'devolver':
            pedido.estado = 'PREPARACION'
            pedido.estado_cocina = 'PENDIENTE'
            motivo = nota_devolucion if nota_devolucion else "Revisar / Calentar pedido"
            aviso = f"⚠️ DEVOLUCIÓN MESERO: {motivo}"

            if pedido.observaciones and pedido.observaciones != "Venta en Caja":
                pedido.observaciones = f"{pedido.observaciones} | {aviso}"
            else:
                pedido.observaciones = aviso

            pedido.save()
            mensaje_respuesta = f"Pedido #{pedido.numero_ticket} devuelto a Cocina con nota."

        elif accion == 'liberar':
            pedido.estado = 'ENTREGADO'
            pedido.save()

            if pedido.mesa_numero and pedido.mesa_numero != 'MESON':
                pedidos_activos = Pedido.objects.filter(
                    mesa_numero=pedido.mesa_numero,
                    estado__in=['PENDIENTE', 'PREPARACION', 'LISTO_ENTREGA', 'SERVIDO']
                ).exists()

                if not pedidos_activos:
                    mesa_obj = Mesa.objects.filter(numero=pedido.mesa_numero).first()
                    if mesa_obj:
                        mesa_obj.estado = 'DISPONIBLE'
                        mesa_obj.save()

            mensaje_respuesta = f"Mesa {pedido.mesa_numero} liberada y disponible."

        else:
            mensaje_respuesta = "Operación completada."

        return JsonResponse({
            'status': 'success',
            'estado': pedido.estado,
            'mensaje': mensaje_respuesta,
            'message': mensaje_respuesta
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def toggle_mesa_view(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        }, status=405)

    try:
        data = json.loads(request.body)
        numero_mesa = str(
            data.get('mesa_numero') or data.get('numero') or ''
        ).strip().upper()
        accion = str(data.get('accion', '')).strip().lower()

        mesa = Mesa.objects.filter(
            numero=numero_mesa
        ).first()

        if not mesa:
            return JsonResponse({
                'status': 'error',
                'message': 'Mesa no encontrada.'
            }, status=404)

        if accion == 'liberar' or mesa.estado == 'OCUPADA':
            mesa.estado = 'DISPONIBLE'
            mesa.save()

            # Cerrar pedidos activos de esta mesa para que no vuelva a marcarse ocupada
            Pedido.objects.filter(
                mesa_numero=numero_mesa,
                estado__in=['PENDIENTE', 'PREPARACION', 'LISTO_ENTREGA', 'SERVIDO']
            ).update(
                estado='ENTREGADO',
                estado_cocina='LISTO',
                estado_barra='LISTO'
            )
        else:
            mesa.estado = 'OCUPADA'
            mesa.save()

        return JsonResponse({
            'status': 'success',
            'nuevo_estado': mesa.estado,
            'numero': mesa.numero
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
def cambiar_estado_pedido_view(request, pedido_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        }, status=405)

    pedido = Pedido.objects.filter(
        id=pedido_id
    ).first()

    if pedido:
        pedido.estado = 'ENTREGADO'
        pedido.estado_cocina = 'LISTO'
        pedido.estado_barra = 'LISTO'
        pedido.save()

        if pedido.mesa:
            pedido.mesa.estado = 'DISPONIBLE'
            pedido.mesa.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Pedido entregado con éxito.',
            'mesa_liberada': pedido.mesa_numero
        })

    return JsonResponse({
        'status': 'error',
        'message': 'Pedido no encontrado.'
    }, status=404)
# ========================================================
# 📊 API: DATOS COMPLETOS PARA PANEL ADMINISTRATIVO
# ========================================================
@csrf_exempt
def api_admin_datos(request):
    from .models import Empleado, Producto, Mesa, CuentaFiado, SegmentacionTerminal, CajaSesion

    try:
        # 1. Consultamos las sesiones abiertas o pausadas en CajaSesion y las cruzamos por username
        sesiones_activas = CajaSesion.objects.select_related('cajero').filter(estado__in=['ABIERTA', 'PAUSADA'])
        estado_turnos = {}
        for s in sesiones_activas:
            if s.cajero:
                esta_pausada = (s.estado == 'PAUSADA')
                estado_turnos[s.cajero.username] = {
                    'en_turno': not esta_pausada,
                    'en_pausa': esta_pausada
                }

        empleados = list(
            Empleado.objects.all().order_by('id').values(
                'id',
                'nombre',
                'user',
                'pass_plain',
                'rol',
                'activo',
                'mostrar_en_login'
            )
        )
        for e in empleados:
            e['pass'] = e.pop('pass_plain')
            info_turno = estado_turnos.get(e['user'], {'en_turno': False, 'en_pausa': False})
            e['en_turno'] = info_turno['en_turno']
            e['en_pausa'] = info_turno['en_pausa']

        productos_qs = Producto.objects.select_related('categoria').filter(activo=True).order_by('id')
        productos = []
        for p in productos_qs:
            productos.append({
                'id': p.id,
                'name': p.nombre,
                'nombre': p.nombre,
                'price': p.precio,
                'precio': p.precio,
                'categoria': p.categoria.codigo if p.categoria else 'comidarapida',
                'tipo_elaboracion': p.tipo_elaboracion
            })

        mesas = list(
            Mesa.objects.all().order_by('id').values('id', 'numero', 'seccion', 'estado')
        )
        mesas_ocupadas = [m['numero'] for m in mesas if m['estado'] == 'OCUPADA']

        fiados_qs = CuentaFiado.objects.select_related('empleado').all().order_by('-deuda', 'id')
        fiados = []
        for f in fiados_qs:
            fiados.append({
                'id': f.id,
                'empleado_id': f.empleado.id if f.empleado else None,
                'nombre': f.empleado.nombre if f.empleado else 'Sin Nombre',
                'rol': f.empleado.rol if f.empleado else 'Personal',
                'ultimoConsumo': f.ultimo_consumo,
                'deuda': f.deuda
            })

        # 2. Cargar segmentación individual por usuario (USER_<username>)
        registros_seg = SegmentacionTerminal.objects.filter(terminal__startswith='USER_')
        usuarios_seg_map = {}
        for r in registros_seg:
            uname = r.terminal.replace('USER_', '', 1)
            usuarios_seg_map[uname] = [c for c in r.categorias.split(',') if c]

        segmentacion_data = {
            'usuarios': usuarios_seg_map
        }

        return JsonResponse({
            'status': 'success',
            'empleados': empleados,
            'productos': productos,
            'productos_admin': productos,
            'mesas': mesas,
            'mesas_ocupadas': mesas_ocupadas,
            'fiados': fiados,
            'segmentacion': segmentacion_data
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    
# ========================================================
# 👥 API: CREAR, MODIFICAR, HABILITAR Y VISIBILIDAD EN LOGIN
# ========================================================
@csrf_exempt
def api_empleados_crud(request):
    from django.contrib.auth.models import User

    if request.method == 'GET':
        empleados = list(
            Empleado.objects.all().order_by('id').values(
                'id',
                'nombre',
                'user',
                'pass_plain',
                'rol',
                'activo',
                'mostrar_en_login'
            )
        )

        for e in empleados:
            e['pass'] = e.pop('pass_plain')

        return JsonResponse({
            'status': 'success',
            'empleados': empleados
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            accion = data.get('accion', 'guardar')
            emp_id = data.get('id')

            # 1. ELIMINAR EMPLEADO (Protegiendo al Administrador)
            if accion == 'eliminar' and emp_id:
                emp = Empleado.objects.filter(id=emp_id).first()

                if emp:
                    if str(emp.rol).strip() == 'Administrador':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'La cuenta del Administrador está protegida.'
                        }, status=400)

                    User.objects.filter(username=emp.user).delete()
                    emp.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Empleado eliminado.'
                })

            # 2. HABILITAR O DESHABILITAR EMPLEADO (Protegiendo al Administrador)
            if accion == 'toggle_estado' and emp_id:
                emp = Empleado.objects.filter(id=emp_id).first()

                if not emp:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Empleado no encontrado.'
                    }, status=404)

                if str(emp.rol).strip() == 'Administrador':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'La cuenta del Administrador no se puede deshabilitar.'
                    }, status=400)

                emp.activo = not emp.activo
                emp.save()

                u = User.objects.filter(username=emp.user).first()
                if u:
                    u.is_active = emp.activo
                    u.save()

                estado_texto = 'habilitada' if emp.activo else 'deshabilitada'
                return JsonResponse({
                    'status': 'success',
                    'activo': emp.activo,
                    'message': f'Cuenta {estado_texto} correctamente.'
                })

            # 2B. MOSTRAR U OCULTAR BOTÓN EN PANTALLA DE LOGIN
            if accion == 'toggle_login' and emp_id:
                emp = Empleado.objects.filter(id=emp_id).first()

                if not emp:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Empleado no encontrado.'
                    }, status=404)

                emp.mostrar_en_login = not emp.mostrar_en_login
                emp.save()

                return JsonResponse({
                    'status': 'success',
                    'mostrar_en_login': emp.mostrar_en_login,
                    'message': 'Visibilidad en login actualizada.'
                })

            # 3. CAPTURA DE DATOS DEL FORMULARIO
            nombre = data.get('nombre', '').strip()
            username_recibido = data.get('user', '')

            if not isinstance(username_recibido, str):
                return JsonResponse({
                    'status': 'error',
                    'message': 'El nombre de usuario no es válido.'
                }, status=400)

            username_limpio = username_recibido.lower().strip()

            if not re.fullmatch(r'[a-z0-9._-]{1,100}', username_limpio):
                return JsonResponse({
                    'status': 'error',
                    'message': (
                        'Usuario inválido: use solo letras, '
                        'números, punto (.), guion (-) '
                        'y guion bajo (_), sin espacios '
                        '(máximo 100 caracteres).'
                    )
                }, status=400)

            password = data.get('pass', '').strip()
            rol = data.get('rol', 'Cajero').strip()

            # 4. EDITAR EMPLEADO EXISTENTE
            if emp_id:
                emp = Empleado.objects.filter(id=emp_id).first()

                if emp:
                    if Empleado.objects.filter(user=username_limpio).exclude(id=emp.id).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': f'El nombre de usuario "{username_limpio}" ya está ocupado por otro registro.'
                        }, status=400)

                    username_viejo = emp.user

                    emp.nombre = nombre
                    emp.user = username_limpio

                    if password:
                        emp.pass_plain = password

                    emp.rol = rol
                    if rol == 'Administrador':
                        emp.activo = True
                    emp.save()

                    u = User.objects.filter(username=username_viejo).first()
                    if u:
                        u.username = username_limpio
                        if password:
                            u.set_password(password)
                        if rol == 'Administrador':
                            u.is_active = True
                        u.save()
                    else:
                        User.objects.get_or_create(
                            username=username_limpio,
                            defaults={
                                'is_active': emp.activo
                            }
                        )

                    return JsonResponse({
                        'status': 'success',
                        'id': emp.id
                    })

            # 5. CREAR NUEVO EMPLEADO
            if Empleado.objects.filter(user=username_limpio).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'El nombre de usuario "{username_limpio}" ya está ocupado.'
                }, status=400)

            u_existente = User.objects.filter(username=username_limpio).first()
            if u_existente:
                u_existente.set_password(password)
                u_existente.is_active = True
                u_existente.save()
            else:
                User.objects.create_user(
                    username=username_limpio,
                    password=password,
                    is_active=True
                )

            nuevo_emp = Empleado.objects.create(
                nombre=nombre,
                user=username_limpio,
                pass_plain=password,
                rol=rol,
                activo=True,
                mostrar_en_login=True
            )

            return JsonResponse({
                'status': 'success',
                'id': nuevo_emp.id
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Falla en el backend de Python: {str(e)}'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido.'
    }, status=405)


# ========================================================
# 🍔 API: PRODUCTOS
# ========================================================

@csrf_exempt
def api_productos_crud(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        accion = data.get('accion', 'guardar')
        prod_id = data.get('id')

        if accion == 'eliminar' and prod_id:
            Producto.objects.filter(id=prod_id).delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Producto eliminado.'
            })

        if accion == 'toggle_activo' and prod_id:
            prod = Producto.objects.filter(
                id=prod_id
            ).first()

            if prod:
                prod.activo = not prod.activo
                prod.save()

                return JsonResponse({
                    'status': 'success',
                    'activo': prod.activo
                })

        nombre = data.get('name', '').strip()
        precio = int(data.get('price', 0))
        cat_codigo = data.get(
            'categoria', 'comidarapida'
        ).strip().lower()

        cat_obj = Categoria.objects.filter(
            codigo=cat_codigo
        ).first()

        if not cat_obj:
            cat_obj = Categoria.objects.create(
                codigo=cat_codigo,
                nombre=cat_codigo.capitalize()
            )

        elab = (
            'BARRA'
            if cat_codigo in [
                'souvenirs',
                'bebestibles',
                'barra',
                'heladeria'
            ]
            else 'COCINA'
        )

        if prod_id:
            prod = Producto.objects.filter(
                id=prod_id
            ).first()

            if prod:
                prod.nombre = nombre
                prod.precio = precio
                prod.categoria = cat_obj
                prod.tipo_elaboracion = elab
                prod.save()

                return JsonResponse({
                    'status': 'success',
                    'id': prod.id
                })

        nuevo_prod = Producto.objects.create(
            nombre=nombre,
            precio=precio,
            categoria=cat_obj,
            tipo_elaboracion=elab,
            activo=True
        )

        return JsonResponse({
            'status': 'success',
            'id': nuevo_prod.id
        })
# ========================================================
# 🍽️ API: MESAS
# ========================================================
@csrf_exempt
def api_mesas_crud(request):
    if request.method == 'GET':
        try:
            mesas = list(
                Mesa.objects.all().values(
                    'id',
                    'numero'
                )
            )

            return JsonResponse({
                'status': 'success',
                'mesas': mesas
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            accion = data.get('accion')
            mesa_id = data.get('id')
            numero_mesa = data.get(
                'numero', ''
            ).strip().upper()

            if accion == 'eliminar' and mesa_id:
                Mesa.objects.filter(
                    id=mesa_id
                ).delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Mesa eliminada con éxito.'
                })

            elif accion == 'guardar' and mesa_id is not None:
                mesa = Mesa.objects.filter(
                    id=mesa_id
                ).first()

                if mesa:
                    if Mesa.objects.filter(
                        numero=numero_mesa
                    ).exclude(
                        id=mesa_id
                    ).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': (
                                f'La Mesa {numero_mesa} '
                                f'ya está registrada.'
                            )
                        })

                    mesa.numero = numero_mesa
                    mesa.save()

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Mesa actualizada correctamente.'
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No se encontró la mesa.'
                    })

            elif accion == 'crear':
                if numero_mesa == "":
                    return JsonResponse({
                        'status': 'error',
                        'message': 'El identificador no puede estar vacío.'
                    })

                if Mesa.objects.filter(
                    numero=numero_mesa
                ).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': (
                            f'La Mesa {numero_mesa} '
                            f'ya existe en el sistema.'
                        )
                    })

                nueva_mesa = Mesa.objects.create(
                    numero=numero_mesa
                )

                return JsonResponse({
                    'status': 'success',
                    'id': nueva_mesa.id,
                    'message': 'Mesa creada con éxito.'
                })

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Acción operativa no reconocida.'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

# ========================================================
# 💳 API: FIADOS (CREAR CONSUMO, EDITAR, LIQUIDAR Y ELIMINAR)
# ========================================================
@csrf_exempt
def api_fiados_crud(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body)
        accion = data.get('accion', 'editar').strip().lower()

        # 1. CREAR O SUMAR CONSUMO FIADO A UN EMPLEADO
        if accion == 'crear':
            emp_id = data.get('empleado_id')
            detalle = data.get('ultimoConsumo', '').strip()
            monto = int(data.get('monto', 0))

            if not emp_id or monto <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Seleccione un empleado y un monto válido.'
                }, status=400)

            empleado_obj = Empleado.objects.filter(id=emp_id).first()
            if not empleado_obj:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Empleado no encontrado.'
                }, status=404)

            fiado = CuentaFiado.objects.filter(empleado_id=empleado_obj.id).first()
            if fiado:
                fiado.deuda = (fiado.deuda or 0) + monto
                if detalle:
                    fiado.ultimo_consumo = detalle
                fiado.save()
            else:
                fiado = CuentaFiado.objects.create(
                    empleado=empleado_obj,
                    ultimo_consumo=detalle or 'Consumo interno',
                    deuda=monto
                )

            return JsonResponse({
                'status': 'success',
                'id': fiado.id,
                'deuda': fiado.deuda
            })

        # 2. BUSCAR CUENTA EXISTENTE PARA EDITAR, LIQUIDAR O ELIMINAR
        fiado_id = data.get('id')
        fiado = CuentaFiado.objects.filter(id=fiado_id).first()

        if not fiado:
            return JsonResponse({
                'status': 'error',
                'message': 'Cuenta de fiado no encontrada.'
            }, status=404)

        if accion == 'eliminar':
            fiado.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Registro de fiado eliminado.'
            })

        elif accion == 'liquidar':
            fiado.deuda = 0
            fiado.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Cuenta consolidada.'
            })

        else:
            monto = int(data.get('deuda', 0))
            fiado.deuda = max(0, monto)
            fiado.save()
            return JsonResponse({
                'status': 'success',
                'deuda': fiado.deuda
            })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error en fiados: {str(e)}'
        }, status=500)
    
# ========================================================
# 📊 6. APIS DE JORNADA (INICIO GLOBAL + PAUSA INDIVIDUAL)
# ========================================================
def _obtener_usuarios_todas_estaciones():
    from django.contrib.auth.models import User

    usuarios = {}
    configs = [
        ('CAJA', 'cajero.safari', 'caja2026'),
        ('COCINA', 'cocina.safari', 'chef2026'),
        ('MESERO', 'mesero.safari', 'garzon2026'),
    ]
    for clave, username, pwd in configs:
        u = User.objects.filter(username=username).first()
        if not u:
            u = User.objects.create_user(username=username, password=pwd, is_active=True)
        usuarios[clave] = u
    return usuarios


def _obtener_usuario_jornada(request, rol_param=''):
    usuarios = _obtener_usuarios_todas_estaciones()
    rol_limpio = str(rol_param or request.session.get('usuario_rol', '')).strip()

    if rol_limpio in ['Cocinero', 'Cocina']:
        return usuarios['COCINA']
    if rol_limpio == 'Mesero':
        return usuarios['MESERO']

    if request.user.is_authenticated and request.user.username not in ['cocina.safari', 'mesero.safari']:
        return request.user
    return usuarios['CAJA']


@csrf_exempt
def abrir_caja_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body) if request.body else {}
        monto_sencillo = int(data.get('monto_apertura', 0))
        rol_param = str(data.get('rol', '')).strip()

        if monto_sencillo < 0:
            return JsonResponse({'status': 'error', 'message': 'El monto inicial no puede ser negativo.'}, status=400)

        usuarios = _obtener_usuarios_todas_estaciones()

        # Si inicia Cajero/Admin, abre jornada para Caja, Cocina y Mesero simultáneamente
        if rol_param in ['', 'Cajero', 'Administrador']:
            sesion_caja = None
            for clave, u_obj in usuarios.items():
                activa = CajaSesion.objects.filter(
                    cajero=u_obj,
                    estado__in=['ABIERTA', 'PAUSADA']
                ).order_by('-id').first()

                if not activa:
                    monto = monto_sencillo if clave == 'CAJA' else 0
                    activa = CajaSesion.objects.create(
                        cajero=u_obj,
                        monto_apertura=monto,
                        estado='ABIERTA'
                    )
                if clave == 'CAJA':
                    sesion_caja = activa

            return JsonResponse({
                'status': 'success',
                'sesion_id': sesion_caja.id if sesion_caja else None,
                'message': 'Turno Iniciado para Caja, Cocina y Mesero.'
            })

        # Si inicia manualmente Cocina o Mesero por separado
        usuario_estacion = _obtener_usuario_jornada(request, rol_param)
        activa = CajaSesion.objects.filter(
            cajero=usuario_estacion,
            estado__in=['ABIERTA', 'PAUSADA']
        ).order_by('-id').first()

        if not activa:
            activa = CajaSesion.objects.create(
                cajero=usuario_estacion,
                monto_apertura=0,
                estado='ABIERTA'
            )

        return JsonResponse({
            'status': 'success',
            'sesion_id': activa.id,
            'message': 'Turno Iniciado Con Éxito.'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def cerrar_caja_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body) if request.body else {}
        rol_param = str(data.get('rol', '')).strip()
        solo_turno_operativo = bool(data.get('solo_turno_operativo', False))
        usuario_estacion = _obtener_usuario_jornada(request, rol_param)

        sesion = CajaSesion.objects.filter(
            cajero=usuario_estacion,
            estado__in=['ABIERTA', 'PAUSADA']
        ).order_by('-id').first()

        # Respaldo multi-pestaña: si la cookie del navegador cambió al cerrar otro rol,
        # buscamos la sesión activa correspondiente a la estación de Caja
        if not sesion and not solo_turno_operativo and rol_param not in ['Cocinero', 'Cocina', 'Mesero']:
            usuarios = _obtener_usuarios_todas_estaciones()
            sesion = CajaSesion.objects.filter(
                cajero=usuarios['CAJA'],
                estado__in=['ABIERTA', 'PAUSADA']
            ).order_by('-id').first()

        if not sesion:
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes ninguna jornada activa. Primero presiona "Iniciar Turno".'
            }, status=404)

        # Cierre individual para Cocina o Mesero
        if solo_turno_operativo or rol_param in ['Cocinero', 'Cocina', 'Mesero']:
            sesion.fecha_cierre = timezone.now()
            sesion.monto_cierre_sistema = 0
            sesion.monto_cierre_real = 0
            sesion.estado = 'CERRADA'
            sesion.save()

            return JsonResponse({
                'status': 'success',
                'solo_turno': True,
                'message': 'Turno operativo finalizado correctamente.'
            })

        # Cierre de Cajero: realiza cuadratura y cierra también las jornadas operativas abiertas
        b20 = max(0, int(data.get('b_20000', 0)))
        b10 = max(0, int(data.get('b_10000', 0)))
        b5 = max(0, int(data.get('b_5000', 0)))
        b1 = max(0, int(data.get('b_1000', 0)))
        m500 = max(0, int(data.get('m_500', 0)))
        m100 = max(0, int(data.get('m_100', 0)))
        m50 = max(0, int(data.get('m_50', 0)))
        m5 = max(0, int(data.get('m_5', 0)))
        m1 = max(0, int(data.get('m_1', 0)))

        total_contado = (
            (b20 * 20000) + (b10 * 10000) + (b5 * 5000) + (b1 * 1000)
            + (m500 * 500) + (m100 * 100) + (m50 * 50) + (m5 * 5) + (m1 * 1)
        )

        ventas_sistema = sum(
            Pedido.objects.filter(
                creado_en__gte=sesion.fecha_apertura,
                estado__in=['ENTREGADO', 'LISTO_ENTREGA', 'SERVIDO']
            ).values_list('total', flat=True)
        )

        ahora = timezone.now()
        sesion.fecha_cierre = ahora
        sesion.monto_cierre_sistema = ventas_sistema
        sesion.monto_cierre_real = total_contado
        sesion.estado = 'CERRADA'
        sesion.save()

        # Cerrar también las sesiones abiertas de Cocina y Mesero al cerrar Caja
        usuarios = _obtener_usuarios_todas_estaciones()
        CajaSesion.objects.filter(
            cajero__in=[usuarios['COCINA'], usuarios['MESERO']],
            estado__in=['ABIERTA', 'PAUSADA']
        ).update(fecha_cierre=ahora, estado='CERRADA')

        CuadraturaDetalle.objects.update_or_create(
            sesion=sesion,
            defaults={
                'b_20000': b20, 'b_10000': b10, 'b_5000': b5, 'b_1000': b1,
                'm_500': m500, 'm_100': m100, 'm_50': m50, 'm_5': m5, 'm_1': m1
            }
        )

        diferencia = total_contado - (sesion.monto_apertura + ventas_sistema)

        return JsonResponse({
            'status': 'success',
            'sistema': ventas_sistema,
            'contado': total_contado,
            'diferencia': diferencia
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
def verificar_estado_caja_api(request):
    """Retorna el estado real de la jornada de cada estación sincronizado con abrir_caja_api."""
    rol_param = str(request.GET.get('rol', '')).strip()
    usuarios = _obtener_usuarios_todas_estaciones()

    if rol_param in ['', 'Cajero', 'Administrador']:
        usuario_estacion = usuarios.get('CAJA') or _obtener_usuario_jornada(request, rol_param)
    else:
        usuario_estacion = _obtener_usuario_jornada(request, rol_param)

    sesion_actual = CajaSesion.objects.filter(
        cajero=usuario_estacion,
        estado__in=['ABIERTA', 'PAUSADA']
    ).order_by('-id').first()

    # Respaldo por si la sesión quedó vinculada al usuario autenticado actual
    if not sesion_actual and request.user.is_authenticated:
        sesion_actual = CajaSesion.objects.filter(
            cajero=request.user,
            estado__in=['ABIERTA', 'PAUSADA']
        ).order_by('-id').first()

    return JsonResponse({
        'status': 'success',
        'necesita_apertura': sesion_actual is None,
        'esta_pausada': (sesion_actual.estado == 'PAUSADA') if sesion_actual else False,
        'bloqueado_por_turno_completado': False
    })

@csrf_exempt
def pausar_caja_api(request):
    """Alterna el estado entre ABIERTA y PAUSADA únicamente para la estación que lo presiona."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body) if request.body else {}
        rol_param = data.get('rol', '')
        usuario_estacion = _obtener_usuario_jornada(request, rol_param)

        sesion = CajaSesion.objects.filter(
            cajero=usuario_estacion,
            estado__in=['ABIERTA', 'PAUSADA']
        ).order_by('-id').first()

        if not sesion:
            return JsonResponse({
                'status': 'error',
                'message': 'No hay ninguna jornada activa para pausar.'
            }, status=404)

        sesion.estado = 'PAUSADA' if sesion.estado == 'ABIERTA' else 'ABIERTA'
        sesion.save()

        return JsonResponse({
            'status': 'success',
            'estado_caja': sesion.estado,
            'message': f'Turno {sesion.estado.lower()} correctamente.'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ========================================================
# 🎯 API: SEGMENTACIÓN POR USUARIO (GUARDADO EN MYSQL)
# ========================================================
@csrf_exempt
def api_segmentacion_terminal(request):
    from .models import SegmentacionTerminal

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            usuario = str(data.get('usuario', '')).strip()
            cats = data.get('categorias', [])

            if not usuario:
                return JsonResponse({'status': 'error', 'message': 'Debe seleccionar un usuario.'}, status=400)

            clave_terminal = f"USER_{usuario}"
            obj, _ = SegmentacionTerminal.objects.get_or_create(
                terminal=clave_terminal,
                defaults={'categorias': 'comidarapida,bebestibles,souvenirs'}
            )
            obj.categorias = ','.join([str(c).strip().lower() for c in cats])
            obj.save()

            return JsonResponse({
                'status': 'success',
                'usuario': usuario,
                'categorias': [c for c in obj.categorias.split(',') if c]
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Si es GET, devolvemos el diccionario completo de todos los usuarios configurados
    registros = SegmentacionTerminal.objects.filter(terminal__startswith='USER_')
    usuarios_map = {}
    for r in registros:
        uname = r.terminal.replace('USER_', '', 1)
        usuarios_map[uname] = [c for c in r.categorias.split(',') if c]

    return JsonResponse({
        'status': 'success',
        'usuarios': usuarios_map
    })