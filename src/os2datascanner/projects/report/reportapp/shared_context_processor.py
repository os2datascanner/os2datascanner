from .utils import user_is
from .models.roles.dpo_model import DataProtectionOfficer
from .models.roles.leader_model import Leader


def check_dpo_and_leader_roles(request):
   """
   This method adds the user roles dpo and/or leader if present
   to all existing views context object.

   This method is referenced from settings.py file and

   Returns a list of roles
   """
   if request.user.is_authenticated:
      user = request.user
      all_roles = user.roles.select_subclasses()
      special_roles = []
      if user_is(all_roles, DataProtectionOfficer):
         special_roles.append(DataProtectionOfficer)
      if user_is(all_roles, Leader):
         special_roles.append(Leader)

      return {
         'roles': special_roles
      }
