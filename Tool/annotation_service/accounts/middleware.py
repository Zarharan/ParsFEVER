from django.shortcuts import redirect


class AuthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != '/accounts/login/' and not request.user.is_authenticated:
            return redirect('/accounts/login')
        response = self.get_response(request)
        return response
