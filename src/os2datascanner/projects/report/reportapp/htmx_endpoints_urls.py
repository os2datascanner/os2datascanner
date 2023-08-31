
from django.urls import path

from .views.report_views import (
  HandleMatchView, MassHandleView, OpenMatchView, ShowMoreMatchesView,
  DistributeMatchesView, DeleteMailView, MassDeleteMailView)

urlpatterns = [
  path('handle_match/<int:pk>/', HandleMatchView.as_view(), name='handle-match'),
  path('mass_handle/', MassHandleView.as_view(), name='mass-handle'),
  path('open_match/<int:pk>/', OpenMatchView.as_view(), name='open-match'),
  path('show_more_matches/<int:pk>/', ShowMoreMatchesView.as_view(), name='show-more-matches'),
  path('distribute/', DistributeMatchesView.as_view(), name='distribute'),
  path('delete_mail/<int:pk>', DeleteMailView.as_view(), name='delete-mail'),
  path('mass_delete_mail/', MassDeleteMailView.as_view(), name="mass-delete-mail")
]
