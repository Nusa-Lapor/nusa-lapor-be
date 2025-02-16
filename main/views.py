from django.shortcuts import render
from django_nextjs.render import render_nextjs_page

# Create your views here.
async def index(request):
    return await render_nextjs_page(request)
