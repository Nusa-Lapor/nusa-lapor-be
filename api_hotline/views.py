from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import Hotline
from .serializers import HotlineSerializer

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def get_hotlines(request: Request):
    """
    Mendapatkan daftar semua layanan hotline
    """
    try:
        hotlines = Hotline.objects.all().order_by('nama')
        serializer = HotlineSerializer(hotlines, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_hotline(request: Request, id_hotline):
    """
    Mendapatkan detail layanan hotline berdasarkan ID
    """
    try:
        hotline = get_object_or_404(Hotline, id_hotline=id_hotline)
        serializer = HotlineSerializer(hotline)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Hotline.DoesNotExist:
        return Response(
            {'error': 'Layanan hotline tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_hotline(request: Request):
    """
    Membuat layanan hotline baru (admin only)
    """
    try:
        serializer = HotlineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Layanan hotline berhasil dibuat',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def update_hotline(request: Request, id_hotline):
    """
    Mengupdate layanan hotline (admin only)
    """
    try:
        hotline = get_object_or_404(Hotline, id_hotline=id_hotline)
        
        # Partial update jika method PATCH
        partial = request.method == 'PATCH'
        
        serializer = HotlineSerializer(
            hotline,
            data=request.data,
            partial=partial
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Layanan hotline berhasil diperbarui',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Hotline.DoesNotExist:
        return Response(
            {'error': 'Layanan hotline tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_hotline(request: Request, id_hotline):
    """
    Menghapus layanan hotline (admin only)
    """
    try:
        hotline = get_object_or_404(Hotline, id_hotline=id_hotline)
        hotline.delete()
        return Response({
            'message': 'Layanan hotline berhasil dihapus'
        }, status=status.HTTP_200_OK)
    except Hotline.DoesNotExist:
        return Response(
            {'error': 'Layanan hotline tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def call_hotline(request: Request, id_hotline):
    """
    Mendapatkan format nomor telepon untuk direct call
    """
    try:
        hotline = get_object_or_404(Hotline, id_hotline=id_hotline)
        tel_number = f"tel:{hotline.nomor_telepon}"
        
        return Response({
            'id_hotline': hotline.id_hotline,
            'nama': hotline.nama,
            'nomor_telepon': hotline.nomor_telepon,
            'tel_link': tel_number,
            'message': f"Menghubungi {hotline.nama} di nomor {hotline.nomor_telepon}"
        }, status=status.HTTP_200_OK)
    except Hotline.DoesNotExist:
        return Response(
            {'error': 'Layanan hotline tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
