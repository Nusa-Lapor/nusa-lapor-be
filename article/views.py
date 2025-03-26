from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Artikel
from .serializers import ArtikelSerializer

# Create your views here.

class ArtikelViewSet(viewsets.ModelViewSet):
    queryset = Artikel.objects.all().order_by('-tanggal_publikasi')
    serializer_class = ArtikelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(penulis=self.request.user.nama)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()
