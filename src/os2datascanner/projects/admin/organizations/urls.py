"""URL patterns for Organizations"""
from django.urls import path

# Must be full path import to allow including url patterns in project urls
from os2datascanner.projects.admin.organizations import views

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organization-list'),
    path('add', views.AddOrganizationView.as_view(), name='add-organization'),
    path('add_for/<uuid:client_id>', views.AddOrganizationView.as_view(),
         name='add-organization-for'),
    path('<slug:slug>/edit', views.UpdateOrganizationView.as_view(), name='edit-organization'),
    path('<slug:org_slug>/units', views.OrganizationalUnitListView.as_view(), name='orgunit-list'),
    path('<slug:slug>/delete', views.DeleteOrganizationView.as_view(), name='delete-organization'),
    path('<slug:slug>/org_delete_blocked',
         views.OrganizationDeletionBlocked.as_view(),
         name='org_delete_block'),
]
