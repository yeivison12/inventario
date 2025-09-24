from django.shortcuts import render

# Create your views here.
def my_custom_page_not_found_view(request, exception):
    return render(request, 'core/404.html', status=404)

def my_custom_permission_denied_view(request, exception):
    return render(request, 'core/403.html', status=403)

def my_custom_error_view(request):
    return render(request, 'core/500.html', status=500)