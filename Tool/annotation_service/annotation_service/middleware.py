from django.shortcuts import redirect
from django.urls import reverse


class WorkInProgressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != reverse('work_in_progress'):
            return redirect(reverse('work_in_progress'))
        response = self.get_response(request)
        return response
