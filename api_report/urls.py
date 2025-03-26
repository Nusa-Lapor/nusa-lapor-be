from django.urls import path
from .views import (
    upload_media,
    save_details,
    finalize_report,
    create_report,
    get_report_by_id,
    get_report_by_user,
    get_report,
    update_report_status,
    assign_report
)

app_name = 'api_report'

urlpatterns = [
    # Report creation process (multi-step)
    path('upload-media/', upload_media, name='upload_media'),
    path('save-details/', save_details, name='save_details'),
    path('finalize-report/', finalize_report, name='finalize_report'),
    
    # Single-step report creation
    path('create-report/', create_report, name='create_report'),
    
    # Report management
    path('<uuid:report_id>/', get_report_by_id, name='get_report'),
    path('<uuid:report_id>/update-status/', update_report_status, name='update_report_status'),
    path('<uuid:report_id>/assign/', assign_report, name='assign_report'),
    path('user/', get_report_by_user, name='get_report_by_user'),
    path('', get_report, name='get_report'),
]