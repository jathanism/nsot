from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    # return HttpResponse('<h1>Shit works!</h1>')
    return render(request, 'app.html')
