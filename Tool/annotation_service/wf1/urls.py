from .views import tutorial, WF1ReviewView, Wf1aView, Wf1bView
from django.urls import path

urlpatterns = [
    path('tutorial/', tutorial, name='tutorial'),
    path('review/', WF1ReviewView.as_view(), name='review-wf1'),
    path('wf1a/', Wf1aView.as_view(), name='wf1a'),
    path('wf1b/<int:source_sentence_id>/', Wf1bView.as_view(), name='wf1b'),
]
