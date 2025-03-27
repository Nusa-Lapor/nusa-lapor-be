import os
from django.forms import ValidationError
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from api_auth.permissions import IsAdmin, IsPetugas
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
from .models import Report, ReportManager
from api_auth.models import User
import json

"""
Method for handling report creation process in multiple steps
"""
@api_view(['POST'])
def upload_media(request: Request):
    VALID_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov']
    file = request.FILES.get('evidance')
    if not file:
        return JsonResponse({'error': 'no file provided'}, status=400)
    
    file = os.path.splitext(file.name)[1].lower()
    if file not in VALID_EXTENSIONS:
        return JsonResponse({'error': 'invalid file type'}, status=400)
    
    request.session['evidance'] = file
    return JsonResponse({'file_name': file}, status=200)

@api_view(['POST'])
def save_details(request: Request):
    data = json.loads(request.body)
    description = data.get('description')
    location = data.get('location')
    if not description or not location:
        return JsonResponse({'error': 'description and location are required'}, status=400)
    
    request.session['description'] = description
    request.session['location'] = location
    return JsonResponse({'message': 'details saved'}, status=200)

@api_view(['POST'])
def finalize_report(request: Request):
    if 'evidance' not in request.session or 'description' not in request.session or 'location' not in request.session:
        return JsonResponse({'error': 'missing data'}, status=400)
    
    evidance = request.session['evidance']
    description = request.session['description']
    location = request.session['location']
    user = request.user
    report = ReportManager.create_report(user, evidance, description, location)

    request.session.clear()

    return JsonResponse({'message': 'report created'}, status=200)

"""
Method for handling report creation process in a single step
"""
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request: Request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        evidance = data.get('evidance')
        description = data.get('description')
        category = data.get('category')
        location = data.get('location')
        if not evidance:
            return JsonResponse({'error': 'Evidance is required'}, status=400)
        if not description:
            return JsonResponse({'error': 'Description is required'}, status=400)
        if not category:
            return JsonResponse({'error': 'Category is required'}, status=400)
        if not location:
            return JsonResponse({'error': 'Location is required'}, status=400)
        
        
        try:
            report = Report.objects.create_report(user, category, evidance, description, location)
            return JsonResponse({
                'message': 'Report successfully created!',
                # 'report': {
                #     'id': report.id_report,
                #     'description': report.description,
                #     'category': report.category,
                #     'location': report.location,
                #     'status': report.status.keterangan,
                #     'created_at': report.created_at,
                # }
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': e}, status=400)
    
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

"""
Method for getting report by ID
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_by_id(request, report_id):
    if request.method == 'GET':
        try:
            report = Report.objects.get(id_report=report_id)
            return JsonResponse(report.to_dict(), status=200)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
"""
Method for getting report by user
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_by_user(request):
    if request.method == 'GET':
        try:
            user = request.user
            reports = Report.objects.filter(id_user=user)
            return JsonResponse({
                'reports': [report.to_dict() for report in reports]
            }, status=200)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'No report found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

"""
Method for getting reports by user role
"""
@api_view(['GET'])
@permission_classes([AllowAny])
def get_report(request):
    if request.method == 'GET':
        try:
            reports = Report.objects.all()
            # Get reports by user role
            if request.user.is_petugas:
                reports = Report.objects.filter(
                    status__keterangan__in=['in_progress', 'completed']
                ).select_related('status').order_by('-created_at')
            elif request.user.is_admin:
                reports = Report.objects.all().order_by('-created_at')
            else:
                reports = Report.objects.exclude(
                    status__keterangan='rejected').order_by('-created_at')

            return JsonResponse({
                'reports': [report.to_dict() for report in reports]
            }, status=200)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

"""
Method for updating report status
"""
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_report_status(request, report_id):
    try:
        user = request.user
        report = Report.objects.get(id_report=report_id)
        data = json.loads(request.body)
        
        new_status = data.get('status')
        detail = data.get('detail')

        if not user.is_petugas and not user.is_admin:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        if user.is_petugas and new_status not in ['in_progress', 'completed']:
            return JsonResponse({'error': 'Invalid status for petugas'}, status=400)
        
        if user.is_admin and new_status not in ['in_progress', 'completed', 'rejected']:
            return JsonResponse({'error': 'Invalid status for admin'}, status=400)

        report.update_status(new_status, detail, request.user)
        
        return JsonResponse({
            'message': 'Status updated successfully',
        }, status=201)
    
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@api_view(['POST'])
@permission_classes([IsAdmin, IsAuthenticated])
def assign_report(request, report_id):
    try:
        report = Report.objects.get(id_report=report_id)
        
        report.assign_officer(request.user)
        
        return JsonResponse({
            'message': 'Report assigned successfully',
            'status': report.get_status()
        })
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsPetugas])
def update_report_status_petugas(request: Request, report_id):
    if request.method == 'POST':
        try:
            report = Report.objects.get(id_report=report_id)
            data = json.loads(request.body)
            
            new_status = data.get('status')
            detail = data.get('detail')
            
            report.update_status_petugas(new_status, detail, request.user)
            
            return JsonResponse({
                'message': 'Status updated successfully',
            }, status=201)
        
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    

    
