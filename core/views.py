import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.db import connection, transaction, DatabaseError
from django.db.models import Sum, Count, F, Q, ProtectedError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Servicio, Categoria, Factura
from .forms import ServicioForm, CategoriaForm, FacturaForm, DetalleFormSet
from . import reportes as reportes_sql


def inicio(request):
    info_bd = connection.settings_dict
    contexto = {
        'motor': info_bd['ENGINE'],
        'host': info_bd['HOST'],
    }
    return render(request, 'core/inicio.html', contexto)


@login_required
def servicios(request):
    lista_servicios = (
        Servicio.objects
        .filter(propietario=request.user)
        .select_related('categoria')
        .order_by('-creado_en', '-id')
    )
    query = request.GET.get('q', '').strip()

    if query:
        lista_servicios = lista_servicios.filter(
            Q(titulo__icontains=query) |
            Q(categoria__nombre__icontains=query)
        )

    paginator = Paginator(lista_servicios, 5)
    pagina = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'core/servicios.html',
        {'servicios': pagina, 'query': query}
    )


@login_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)

        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.propietario = request.user
             # save(): no se toca
            nuevo.save()
            # messages.success: NUEVO; se guarda ahora y se muestra una vez en la siguiente página
            messages.success(request, f'Servicio "{nuevo.titulo}" creado.')
            # redirect: el listado usa base.html, que ya dibuja los mensajes
            return redirect('servicios')
    else:
        form = ServicioForm()

    return render(
        request,
        'core/servicio_form.html',
        {'form': form, 'titulo_pagina': 'Nuevo servicio'}
    )


@login_required
def editar_servicio(request, pk):
    servicio = get_object_or_404(
        Servicio,
        pk=pk,
        propietario=request.user
    )

    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)

        if form.is_valid():
            form.save()
            return redirect('servicios')
    else:
        form = ServicioForm(instance=servicio)

    return render(
        request,
        'core/servicio_form.html',
        {'form': form, 'titulo_pagina': 'Editar servicio'}
    )


@login_required
def eliminar_servicio(request, pk):
    servicio = get_object_or_404(
        Servicio,
        pk=pk,
        propietario=request.user
    )

    if request.method == 'POST':
        try:
            servicio.delete()
            messages.success(request, f'Se eliminó "{servicio.titulo}".')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{servicio.titulo}": '
                'ya aparece en una factura.'
            )
        return redirect('servicios')

    return render(
        request,
        'core/servicio_confirm_delete.html',
        {'servicio': servicio}
    )


@login_required
def categorias(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada.')
            return redirect('categorias')
    else:
        form = CategoriaForm()

    lista = Categoria.objects.annotate(
        total_servicios=Count(
            'servicios',
            filter=Q(servicios__propietario=request.user)
        )
    )

    return render(
        request,
        'core/categorias.html',
        {'form': form, 'categorias': lista}
    )


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)

        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada.')
            return redirect('categorias')
    else:
        form = CategoriaForm(instance=categoria)

    return render(
        request,
        'core/categoria_form.html',
        {'form': form}
    )


@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(
                request,
                f'Se eliminó la categoría "{categoria.nombre}".'
            )
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{categoria.nombre}": '
                'todavía tiene servicios.'
            )

    return redirect('categorias')


@login_required
def facturas(request):
    lista = (
        Factura.objects
        .filter(usuario=request.user)
        .annotate(
            total=Sum(
                F('detalles__cantidad') *
                F('detalles__precio_unitario')
            ),
            partidas=Count('detalles')
        )
        .order_by('-fecha', '-id')
    )

    pagina = Paginator(lista, 10).get_page(request.GET.get('page'))

    return render(
        request,
        'core/facturas.html',
        {'facturas': pagina}
    )


@login_required
def crear_factura(request):
    factura = Factura(usuario=request.user)

    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        formset = DetalleFormSet(
            request.POST,
            instance=factura,
            form_kwargs={'usuario': request.user}
        )

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                factura = form.save()
                detalles = formset.save(commit=False)

                for detalle in detalles:
                    detalle.precio_unitario = detalle.servicio.precio
                    detalle.save()

            messages.success(request, f'Factura {factura.folio} guardada.')
            return redirect('detalle_factura', pk=factura.pk)
    else:
        form = FacturaForm(instance=factura)
        formset = DetalleFormSet(
            instance=factura,
            form_kwargs={'usuario': request.user}
        )

    return render(
        request,
        'core/factura_form.html',
        {'form': form, 'formset': formset}
    )


@login_required
def detalle_factura(request, pk):
    factura = get_object_or_404(
        Factura,
        pk=pk,
        usuario=request.user
    )
    detalles = factura.detalles.select_related('servicio__categoria')
    total = detalles.aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or 0

    return render(
        request,
        'core/factura_detalle.html',
        {
            'factura': factura,
            'detalles': detalles,
            'total': total
        }
    )


@login_required
def reportes(request):
    return render(
        request,
        'core/reportes.html',
        {'consultas': reportes_sql.CONSULTAS}
    )


@login_required
def reporte(request, clave):
    consulta = reportes_sql.buscar(clave)

    if consulta is None:
        raise Http404('Reporte no encontrado')

    parametros = {'uid': request.user.id}
    ver_plan = request.GET.get('plan') == '1'
    sql = 'EXPLAIN ' + consulta['sql'] if ver_plan else consulta['sql']
    error = None

    try:
        columnas, filas, milisegundos = reportes_sql.ejecutar_sql(
            sql,
            parametros
        )
    except DatabaseError as e:
        columnas, filas, milisegundos, error = [], [], 0, str(e)

    if request.GET.get('formato') == 'csv' and error is None:
        respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="{clave}.csv"'
        )
        respuesta.write('\ufeff')
        escritor = csv.writer(respuesta)
        escritor.writerow(columnas)
        escritor.writerows(filas)
        return respuesta

    celdas = [
        [reportes_sql.formatear(valor) for valor in fila]
        for fila in filas
    ]

    contexto = {
        'consulta': consulta,
        'sql_mostrado': sql.strip(),
        'columnas': columnas,
        'filas': celdas,
        'milisegundos': round(milisegundos, 1),
        'ver_plan': ver_plan,
        'error': error,
    }

    return render(request, 'core/reporte.html', contexto)


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            usuario_nuevo = form.save()
            login(request, usuario_nuevo)
            messages.success(
                request,
                f'Cuenta creada. ¡Bienvenido, {usuario_nuevo.username}!'
            )
            return redirect('servicios')
    else:
        form = UserCreationForm()

    return render(
        request,
        'core/registro.html',
        {'form': form}
    )


def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Sesión iniciada correctamente.')
            return redirect('servicios')
    else:
        form = AuthenticationForm()

    return render(
        request,
        'core/login.html',
        {'form': form}
    )


def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')