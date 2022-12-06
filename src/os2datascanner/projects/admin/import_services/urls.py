"""URL patterns for Directory Services"""
from django.urls import path

# Must be full path import to allow including url patterns in project urls
from os2datascanner.projects.admin.import_services import views


urlpatterns = [
     path('ldap/add/<uuid:org_id>',
          views.LDAPAddView.as_view(),
          name='add-ldap'),
     path('ldap/edit/<uuid:pk>',
          views.LDAPUpdateView.as_view(),
          name='edit-ldap'),
     path('ldap/test/connection',
          views.verify_connection,
          name='test-ldap-connection'),
     path('ldap/test/authentication',
          views.verify_authentication,
          name='test-ldap-authentication'),
     path('ldap/import/<uuid:pk>',
          views.LDAPImportView.as_view(),
          name='import-ldap'),
     path('msgraph-organization/add/<uuid:org_id>',
          views.MSGraphAddView.as_view(),
          name='add-msgraph'),
     path('msgraph-organization/add/<uuid:org_id>/',
          views.MSGraphAddView.as_view(),
          name='add-msgraph'),
     path('msgraph-organization/edit/<uuid:pk>',
          views.MSGraphUpdateView.as_view(),
          name='edit-msgraph'),
     path('msgraph-organization/import/<uuid:pk>',
          views.MSGraphImportView.as_view(),
          name='import-msgraph'),
     path('os2mo-organization/add/<uuid:org_id>',
          views.OS2moAddView.as_view(),
          name='add-os2mo'),
     path('os2mo-organization/import/<uuid:pk>',
          views.OS2moImportView.as_view(),
          name='import-os2mo'),
]
