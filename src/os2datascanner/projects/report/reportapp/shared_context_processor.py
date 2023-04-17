from .utils import user_is
from .models.roles.role import Role
from .models.roles.dpo import DataProtectionOfficer


def check_dpo_roles(request):
    """
    This method adds the user role dpo if present
    to all existing views context object.

    This method is referenced from settings.py file and

    Returns a list of roles
    """
    special_roles = []
    if request.user.is_authenticated:
        all_roles = Role.get_user_roles_or_default(request.user)
        if user_is(all_roles, DataProtectionOfficer):
            special_roles.append(DataProtectionOfficer)

    return {
        'roles': special_roles
    }
