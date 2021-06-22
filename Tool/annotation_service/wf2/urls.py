from .views import Wf2View, CheckSentencesView, WF2ReviewView
from django.urls import path

urlpatterns = [
    path('', Wf2View.as_view(), name='wf2'),
    path('review/', WF2ReviewView.as_view(), name='review-wf2'),
    path('check_sentences/', CheckSentencesView.as_view(), name='check_sentences'),
]
