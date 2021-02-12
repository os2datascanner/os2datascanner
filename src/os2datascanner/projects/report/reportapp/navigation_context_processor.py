from .models.roles.defaultrole_model import DefaultRole


def navigation_items(request):
    user = request.user
    roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
    return {
       'nav_items': [role.__class__.__name__ for role in roles],
    }
