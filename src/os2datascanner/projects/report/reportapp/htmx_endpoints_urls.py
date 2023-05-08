
from django.urls import path

from .views.report_views import (HandleMatchView, MassHandleView, OpenMatchView)

urlpatterns = [
  path('handle_match/<int:pk>/', HandleMatchView.as_view(), name='handle-match'),
  path('mass_handle/', MassHandleView.as_view(), name='mass-handle'),
  path('open_match/<int:pk>/', OpenMatchView.as_view(), name='open-match'),
]
