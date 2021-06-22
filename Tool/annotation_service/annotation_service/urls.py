"""annotation_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from annotation_service.views import index_view, validate_textbox_view, get_user_pages_view, save_mutation_view, \
    statistics_update_view, supervisor_check_view, work_in_progress_view, get_sentence_hyperlinks_view, \
    add_evidence_view, update_claim_state_view, annotate_view, submit_wf2_view, get_user_completed_claims_view, \
    delete_label_view, edit_claim_view
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', index_view, name='index'),
    path('work_in_progress/', work_in_progress_view, name='work_in_progress'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('wf1/', include('wf1.urls')),
    path('wf2/', include('wf2.urls')),
    path('reports/', include('reports.urls')),
    path('ajax/validate_textbox/', validate_textbox_view, name='validate_textbox'),
    path('ajax/get_user_pages/', get_user_pages_view, name='get_user_pages'),
    path('ajax/save_mutation/', save_mutation_view, name='save_mutation'),
    path('ajax/statistics_update/', statistics_update_view, name='statistics_update'),
    path('ajax/supervisor_check/', supervisor_check_view, name='supervisor_check'),
    path('ajax/get_sentence_hyperlinks/', get_sentence_hyperlinks_view, name='get_sentence_hyperlinks'),
    path('ajax/add_evidence/', add_evidence_view, name='add_evidence'),
    path('ajax/update_claim_state/', update_claim_state_view, name='update_claim_state'),
    path('ajax/annotate/', annotate_view, name='annotate'),
    path('ajax/submit_wf2/', submit_wf2_view, name='submit_wf2'),
    path('ajax/get_user_completed_claims/', get_user_completed_claims_view, name='get_user_completed_claims'),
    path('ajax/delete_label/', delete_label_view, name='delete_label'),
    path('ajax/edit_claim/', edit_claim_view, name='edit_claim'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
