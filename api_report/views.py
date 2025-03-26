import os
from django.forms import ValidationError
from django.shortcuts import render
import hashlib, base64
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
from .models import Report, ReportManager
import json

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

@api_view(['POST'])
def create_report(request: Request):
    if request.method == 'POST':
        # user = request.user
        
        # if not user.is_authenticated:
        #     return JsonResponse({'error': 'authentication required'}, status=401)
        user = None

        evidance = request.FILES.get('evidance')
        description = request.POST.get('description')
        category = request.POST.get('category')
        location = request.POST.get('location')
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
            response_data = {
                'id': str(report.id_report),
                'description': report.description,
                'category': report.category,
                'location': report.location,
                'created_at': report.created_at.isoformat(),
                'status': {
                    'keterangan': report.status.keterangan,
                    'detail_status': report.status.detail_status,
                    'waktu_update': report.status.waktu_update.isoformat()
                } if hasattr(report, 'status') else None
            }

            # Add image data if exists
            if report.evidance:
                # Option 2: Return base64 encoded image
                try:
                    with open(report.evidance.path, 'rb') as img_file:
                        encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
                        file_ext = os.path.splitext(report.evidance.name)[1].lstrip('.')
                        response_data['evidance_base64'] = f"data:image/{file_ext};base64,{encoded_image}"
                except Exception as e:
                    response_data['evidance_error'] = str(e)

            return JsonResponse(response_data, status=200)
            # return JsonResponse({
            #     'message': 'Report successfully created!',
            #     'report': {
            #         'id': report.id_report,
            #         'description': report.description,
            #         'category': report.category,
            #         'location': report.location,
            #         'status': report.status.keterangan,
            #         'created_at': report.created_at,
            #     }
            # }, status=201)
        except Exception as e:
            return JsonResponse({'error': e}, status=400)
    
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def get_report_by_id(request, report_id):
    if request.method == 'GET':
        try:
            report = Report.objects.get(id_report=report_id)
            return JsonResponse(report.to_dict(), status=200)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@api_view(['GET'])
def get_report_by_user(request):
    if request.method == 'GET':
        try:
            user = request.user
            reports = Report.objects.filter(user=user)
            return JsonResponse({
                'reports': [report.to_dict() for report in reports]
            }, status=200)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'No report found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def get_report(request):
    if request.method == 'GET':
        try:
            # Get reports excluding rejected and completed status
            reports = Report.objects.exclude(
                status__keterangan__in=['rejected', 'completed']
            ).select_related('status')

            return JsonResponse({
                'reports': [report.to_dict() for report in reports]
            }, status=200)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['POST'])
def update_report_status(request, report_id):
    try:
        report = Report.objects.get(id_report=report_id)
        data = json.loads(request.body)
        
        new_status = data.get('status')
        detail = data.get('detail')
        
        report.update_status(new_status, detail, request.user)
        
        return JsonResponse({
            'message': 'Status updated successfully',
        }, status=201)
    
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
# To be implemented in the future
@api_view(['POST'])
def assign_report(request, report_id):
    try:
        report = Report.objects.get(id_report=report_id)
        
        # Assign officer (assuming current user is an officer)
        report.assign_officer(request.user)
        
        return JsonResponse({
            'message': 'Report assigned successfully',
            'status': report.get_status()
        })
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    

    
