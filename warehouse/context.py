from .access import role
def navigation(request):
    return {'current_role': role(request.user) if request.user.is_authenticated else '',
            'nav_items': [('dashboard','◫','Resumen'),('products','▦','Inventario'),('movement_new','⇄','Operaciones de stock'),('movements','↺','Movimientos'),('reports','▥','Reportes'),('locations','⌖','Ubicaciones')]}
