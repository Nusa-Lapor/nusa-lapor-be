from django.shortcuts import render
from django.http import HttpResponse
# from django_nextjs.render import render_nextjs_page

# Create your views here.
async def index(request):
    # return await render_nextjs_page(request)
    return HttpResponse("<h1>Selamat Datang di NusaLapor</h1><p>Server Django berhasil berjalan</p>")