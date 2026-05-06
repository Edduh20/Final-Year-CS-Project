from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Sum, Count
from django.db.models.functions import Lower
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal
from django.http import HttpResponse
from PIL import Image
import os
from django.core.mail import send_mail
import random
import string
import uuid
from core.mpesa_service import mpesa_service
from django.conf import settings
from reportlab.graphics.shapes import Drawing, Polygon
import math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Lobster', os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Lobster-Regular.ttf')))

from .models import (
    UserProfile, LandRecord, Document, Transaction,
    Notification,  LegalCaseSubmission, OwnershipHistory,
)
from .serializers import (
    UserProfileSerializer,
    LandRecordListSerializer, LandRecordDetailSerializer, LandRecordCreateSerializer,
    DocumentListSerializer, DocumentDetailSerializer, DocumentCreateSerializer, DocumentVerificationSerializer,
    TransactionListSerializer, TransactionDetailSerializer, TransactionCreateSerializer,
    NotificationSerializer, StatisticsSerializer, PaymentInitiationSerializer, PaymentCallbackSerializer,
    LegalCaseCreateSerializer, LegalCaseSubmissionSerializer, OwnershipHistorySerializer
)
from .permissions import IsAdmin, IsLandOfficer, IsLegalOfficer, IsOwnerOrOfficer
from .utils import process_ocr, initiate_mpesa_payment

from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.graphics.shapes import Drawing, Polygon
from io import BytesIO
from datetime import datetime



# ===================== USER MANAGEMENT =====================
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        id_number = self.request.query_params.get('id_number')
        if id_number:
            all_users = UserProfile.objects.exclude(user_id_number__isnull=True).exclude(user_id_number='')
    
            users = UserProfile.objects.filter(user_id_number__iexact=id_number.strip())
            
            return users

        if user.user_role in ['admin', 'superadmin']:
            return UserProfile.objects.filter(user_is_registered=True)


        elif user.user_role == 'land_officer':
            return UserProfile.objects.filter(user_role='user')


        elif user.user_role == 'legal_officer':
            return UserProfile.objects.filter(user_role='user')


        return UserProfile.objects.filter(pk=user.pk)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        
        new_user.generate_otp()

        admin_user = request.user  

        Notification.objects.create(
            notification_user_id=admin_user,
            notification_title='User Created Successfully',
            notification_message=f'You created an account for {new_user.user_full_name} ({new_user.user_role.replace("_", " ").title()}).',
            notification_type='success'
        )

        Notification.objects.create(
            notification_user_id=new_user,
            notification_title='Welcome to TitleGuard!',
            notification_message=f'Your account has been created successfully. You can now log in using your email: {new_user.user_email}',
            notification_type='info'
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            admin_user = request.user
            
            self.perform_update(serializer)
            
            return Response(serializer.data)
            
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return Response(
                {'error': f'Failed to update user: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_update(self, serializer):
        """Notify when user profile is updated"""
        try:
            updated_user = serializer.save()
            admin_user = self.request.user

            if admin_user.user_id == updated_user.user_id:
                Notification.objects.create(
                    notification_user_id=updated_user,
                    notification_title='Profile Updated',
                    notification_message='Your profile has been successfully updated.',
                    notification_type='success'
                )
            else:
                Notification.objects.create(
                    notification_user_id=admin_user,
                    notification_title='User Updated',
                    notification_message=f"You updated {updated_user.user_full_name}'s account information.",
                    notification_type='success'
                )
                Notification.objects.create(
                    notification_user_id=updated_user,
                    notification_title='Account Updated',
                    notification_message='Your account information has been updated by an administrator.',
                    notification_type='info'
                )
        except Exception as e:
            print(f"Error in perform_update: {str(e)}")
            
    

    def perform_destroy(self, instance):
        try:
            admin_user = self.request.user
            deleted_name = instance.user_full_name  
            deleted_email = instance.user_email

            Notification.objects.filter(notification_user_id=instance).delete()


            LandRecord.objects.filter(land_records_owner_id=instance).update(
                land_records_owner_id=None
            )
            
            LandRecord.objects.filter(land_records_previous_owner=instance).update(
                land_records_previous_owner=None
            )
            

            Transaction.objects.filter(transaction_from_owner_id=instance).update(
                transaction_from_owner_id=None
            )
            Transaction.objects.filter(transaction_to_owner_id=instance).update(
                transaction_to_owner_id=None
            )
            Transaction.objects.filter(transaction_legal_officer_id=instance).update(
                transaction_legal_officer_id=None
            )
            Transaction.objects.filter(transaction_land_officer_id=instance).update(
                transaction_land_officer_id=None
            )
            

            
            

            LegalCaseSubmission.objects.filter(case_legal_officer=instance).update(
                case_legal_officer=None
            )
            

            OwnershipHistory.objects.filter(history_previous_owner=instance).update(
                history_previous_owner=None
            )
            OwnershipHistory.objects.filter(history_new_owner=instance).update(
                history_new_owner=None
            )
            


            instance.delete()

            Notification.objects.create(
                notification_user_id=admin_user,
                notification_title='User Deleted Successfully',
                notification_message=f'User "{deleted_name}" ({deleted_email}) has been deleted from the system.',
                notification_type='warning'
            )

        except Exception as e:
            raise exception


    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


    @action(detail=False, methods=['patch'], url_path='update_profile')
    def update_profile(self, request):
        user = request.user

    
        try:
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()
        
        
            Notification.objects.create(
                notification_user_id=user,
                notification_title='Profile Updated',
                notification_message='Your profile has been updated successfully.',
                notification_type='success'
            )
        
            return Response(serializer.data)
        
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            return Response(
                {'error': f'Failed to update profile: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role = request.query_params.get('role')
        if not role:
            return Response({'error': 'Role parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        profiles = self.queryset.filter(role=role)
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)


# ===================== LAND RECORDS =====================
class LandRecordViewSet(viewsets.ModelViewSet):
    queryset = LandRecord.objects.select_related('land_records_owner_id').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['land_records_parcel_number', 'land_records_deed_number', 'land_records_location', 'land_records_owner_id__user_full_name', 'land_records_owner_id__user_id_number']
    ordering_fields = ['land_records_created_at', 'land_records_verification_status', 'land_records_size']
    ordering = ['-land_records_created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return LandRecordListSerializer
        elif self.action == 'create':
            return LandRecordCreateSerializer
        return LandRecordDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user


        if user.user_role == 'user':
            queryset = queryset.filter(
                land_records_owner_id=user,
                land_records_verification_status__in=['pending', 'verified']
            )

        elif user.user_role == 'land_officer':
            if user.user_county:
                queryset = queryset.filter(land_records_county__iexact=user.user_county)  
            else:
                queryset = queryset.none()


        elif user.user_role == 'legal_officer':
            if user.user_county:
                queryset = queryset.filter(
                    land_records_county__iexact=user.user_county, 
                    land_records_verification_status='flagged'
                )
            else:
                queryset = queryset.none()

        elif user.user_role in ['admin', 'superadmin']:
            queryset = queryset.all()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(land_records_verification_status=status_filter)

        county_filter = self.request.query_params.get('county')
        if county_filter and user.user_role in ['admin', 'superadmin']:
            queryset = queryset.filter(land_records_county__iexact=county_filter)  

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.user_role == 'user':
            record = serializer.save(land_records_owner_id=user, land_records_verification_status='pending')
            Notification.objects.create(
                notification_user_id=user,
                notification_title='Land Record Submitted',
                notification_message=f'Your land record {record.land_records_parcel_number} has been submitted for verification.',
                notification_type='info'
            )

        elif user.user_role == 'land_officer':
            record = serializer.save(land_records_owner_id=user, land_records_verification_status='verified')
            Notification.objects.create(
                notification_user_id=user,
                notification_title='Land Record Added',
                notification_message=f'Land record {record.land_records_parcel_number} has been successfully added.',
                notification_type='success'
            )

        elif user.user_role in ['admin', 'superadmin']:
            record = serializer.save(land_records_verification_status='verified')
            

            Notification.objects.create(
                notification_user_id=user,
                notification_title='Land Record Created',
                notification_message=f'Land record {record.land_records_parcel_number} has been successfully created.',
                notification_type='success'
            )
            

            if record.land_records_owner_id:
                Notification.objects.create(
                    notification_user_id=record.land_records_owner_id,
                    notification_title='Land Record Registered',
                    notification_message=f'A land record {record.land_records_parcel_number} has been registered in your name.',
                    notification_type='info'
                )
            

            if record.land_records_county:
                land_officers = UserProfile.objects.filter(
                    user_role='land_officer',
                    user_county__iexact=record.land_records_county,
                    user_is_active=True
                )
                
                for officer in land_officers:
                    Notification.objects.create(
                        notification_user_id=officer,
                        notification_title='New Land Record Added to Your County',
                        notification_message=(
                            f'A new land record {record.land_records_parcel_number} has been added to '
                            f'{record.land_records_county.replace("_", " ").title()} County by an administrator. '
                            f'Location: {record.land_records_location}'
                        ),
                        notification_type='info',
                        notification_related_entity_type='land_record',
                        notification_related_entity_id=record.land_records_id
                    )
                

    @action(detail=True, methods=['post'], permission_classes=[IsLandOfficer])
    def update_status(self, request, pk=None):
        land_record = self.get_object()
        new_status = request.data.get('verification_status')

        if new_status not in ['pending', 'verified', 'rejected', 'flagged']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        land_record.land_records_verification_status = new_status
        land_record.save()


        if land_record.land_records_owner_id:
            Notification.objects.create(
                notification_user_id=land_record.land_records_owner_id,
                notification_title=f'Land Record {new_status.capitalize()}',
                notification_message=f'Your land record {land_record.land_records_parcel_number} has been {new_status}.',
                notification_type='success' if new_status == 'verified' else 'warning'
            )

        serializer = self.get_serializer(land_record)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='search', permission_classes=[IsAuthenticated])
    def search(self, request):
        query = request.query_params.get('id_number', '').strip()
        if not query:
            return Response({"error": "ID number or parcel/deed number required"}, status=status.HTTP_400_BAD_REQUEST)


        records = LandRecord.objects.filter(
            Q(land_records_owner_id__user_id_number__iexact=query) |
            Q(land_records_parcel_number__iexact=query) |
            Q(land_records_deed_number__iexact=query),
        )

        serializer = LandRecordListSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        """
        Admin bulk upload of land records via CSV or Excel using ID numbers.
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read file (CSV or Excel)
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return Response(
                    {'error': 'Unsupported file type. Please upload CSV or Excel.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            required_cols = [
                'parcel_number',
                'deed_number',
                'id_number',
                'location',
                'county',
                'size_hectares'
            ]
            for col in required_cols:
                if col not in df.columns:
                    return Response(
                        {'error': f'Missing column "{col}" in uploaded file.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            created_count = 0
            skipped_rows = []
            county_records = {} 
            owner_records = {}  

            for _, row in df.iterrows():
                try:
                    owner = None
                    if pd.notna(row['id_number']):
                        owner = UserProfile.objects.filter(user_id_number=str(row['id_number']).strip()).first()

                    record = LandRecord.objects.create(
                        land_records_parcel_number=row['parcel_number'],
                        land_records_deed_number=row['deed_number'],
                        land_records_owner_id=owner,
                        land_records_location=row['location'],
                        land_records_county=row['county'],
                        land_records_size=row['size_hectares'],
                        land_records_verification_status='pending'
                    )
                    created_count += 1
                    
                    county = row['county']
                    if county not in county_records:
                        county_records[county] = []
                    county_records[county].append(record.land_records_parcel_number)
                    
                    if owner:
                        if owner.user_id not in owner_records:
                            owner_records[owner.user_id] = []
                        owner_records[owner.user_id].append(record.land_records_parcel_number)
                    
                except Exception as e:
                    skipped_rows.append(str(e))
                    continue

            for county, parcels in county_records.items():
                land_officers = UserProfile.objects.filter(
                    user_role='land_officer',
                    user_county__iexact=county,
                    user_is_active=True
                )
                
                for officer in land_officers:
                    parcel_list = ", ".join(parcels[:5])
                    if len(parcels) > 5:
                        parcel_list += f" and {len(parcels) - 5} more"
                    
                    Notification.objects.create(
                        notification_user_id=officer,
                        notification_title=f'New Land Records in {county} County',
                        notification_message=(
                            f'{len(parcels)} new land record(s) have been added to {county.replace("_", " ").title()} County '
                            f'via bulk upload. Parcels: {parcel_list}'
                        ),
                        notification_type='info',
                        notification_related_entity_type='land_record'
                    )


            for owner_id, parcels in owner_records.items():
                owner = UserProfile.objects.get(user_id=owner_id)
                parcel_list = ", ".join(parcels[:3])  
                if len(parcels) > 3:
                    parcel_list += f" and {len(parcels) - 3} more"
                
                Notification.objects.create(
                    notification_user_id=owner,
                    notification_title='Land Records Registered in Your Name',
                    notification_message=(
                        f'{len(parcels)} land record(s) have been registered in your name via bulk upload. '
                        f'Parcels: {parcel_list}. Status: Pending Verification'
                    ),
                    notification_type='info',
                    notification_related_entity_type='land_record'
                )


            admin_user = request.user
            Notification.objects.create(
                notification_user_id=admin_user,
                notification_title='Bulk Upload Completed',
                notification_message=(
                    f'Successfully uploaded {created_count} land records to the system. '
                    f'{len(skipped_rows)} records were skipped due to errors.'
                ),
                notification_type='success' if created_count > 0 else 'warning'
            )

            message = f"{created_count} records uploaded successfully."
            if skipped_rows:
                message += f" {len(skipped_rows)} records skipped due to errors."


            return Response({'message': message}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Bulk upload error:", e)
            
            if request.user:
                Notification.objects.create(
                    notification_user_id=request.user,
                    notification_title='Bulk Upload Failed',
                    notification_message=f'Bulk upload failed with error: {str(e)}',
                    notification_type='error'
                )
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['GET'], url_path="ownership-history")
    def get_ownership_history(self, request, pk=None):
        land_record = self.get_object()

        # Permission: Admin, Land Officer, Legal Officer, or the Owner
        if not (
            request.user.is_superuser
            or request.user.user_role in ['admin', 'land_officer', 'legal_officer']
            or land_record.land_records_owner_id == request.user
        ):
            return Response({"error": "You are not allowed to view this history."}, status=403)

        history = land_record.ownership_history.order_by('-history_transfer_date')
        serializer = OwnershipHistorySerializer(history, many=True)
        return Response(serializer.data)


#============SEARCH LAND RECORDS=====================#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_land_records(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return Response({'error': 'Search query is required'}, status=400)

    records = LandRecord.objects.select_related('land_records_owner_id').filter(
        Q(land_records_parcel_number__icontains=query) |
        Q(land_records_deed_number__icontains=query) |
        Q(land_records_owner_id__user_id_number__icontains=query)
    )

    serializer = LandRecordDetailSerializer(records, many=True)
    return Response(serializer.data)


# ===================== TITLE DEED DOWNLOAD =====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_land_deed(request, land_record_id):
    """
    Download land record deed as PDF
    """
    try:
        land_record = LandRecord.objects.select_related('land_records_owner_id').get(
            land_records_id=land_record_id
        )
    except LandRecord.DoesNotExist:
        return Response({'error': 'Land record not found'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user


    if not (
        land_record.land_records_owner_id == user
        or user.user_role in ['land_officer', 'legal_officer', 'admin']
    ):
        return Response({'error': 'You do not have permission to download'}, status=403)


    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=40)
    elements = []
    styles = getSampleStyleSheet()

  
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=40, fontName='Lobster', alignment=1, leading=32)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, alignment=1)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=12, leading=16)
    small_center = ParagraphStyle('SmallCenter', parent=styles['Normal'], fontSize=10, alignment=1)

 
    elements.append(Paragraph("REPUBLIC OF KENYA", header_style))
    elements.append(Spacer(1, 4))

    try:
        coat_path = os.path.join(settings.BASE_DIR, "static", "coat_of_arms.png")
        elements.append(Image(coat_path, width=75, height=75))
    except:
        elements.append(Paragraph("[Coat of Arms Missing]", normal_style))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("THE LAND REGISTRATION ACT", small_center))
    elements.append(Paragraph("(No. 3 of 2012, Section 108)", small_center))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Title Deed</b>", title_style))
    elements.append(Spacer(1, 10))


    elements.append(Paragraph(
        f"Title Number: <b>{land_record.land_records_parcel_number}</b>", normal_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        f"Approximate Area: <b>{land_record.land_records_size} Ha.</b>", normal_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        f"Deed Number: <b>{land_record.land_records_deed_number}</b>", normal_style
    ))
    elements.append(Spacer(1, 12))


    owner = land_record.land_records_owner_id
    owner_name = owner.user_full_name if owner else "N/A"
    owner_id = owner.user_id_number if owner else "N/A"

    cert_text = f"""
    <i>This is to certify that</i> <b>{owner_name}</b> of
    ID No. <b>{owner_id}</b><br/><br/>
    is now registered as the absolute proprietor of the land comprised in the above-mentioned title,
    subject to the entries in the register relating to the land and to such of the overriding interests 
    set out in section 28 of the Land Registration Act (No. 3 of 2012) 
    as may for the time being subsist and affect the land.
    """

    elements.append(Paragraph(cert_text, normal_style))
    elements.append(Spacer(1, 25))


    reg_date = land_record.land_records_registered_date


    def starburst_points(cx, cy, r, spikes):
        import math
        pts = []
        ang = math.pi / spikes
        for i in range(spikes * 2):
            rr = r if i % 2 == 0 else r * 0.82
            x = cx + math.cos(i * ang) * rr
            y = cy + math.sin(i * ang) * rr
            pts.extend([x, y])
        return pts

    seal = Drawing(180, 180)
    seal.add(
        Polygon(
            starburst_points(90, 90, 80, spikes=40),
            fillColor=colors.HexColor("#d94d59"),
            strokeColor=colors.HexColor("#b13844"),
            strokeWidth=1.5
        )
    )


    county = land_record.land_records_county
    registrar_name = f"{county} Land Registrar"


    given_text = Paragraph(
        f"GIVEN under my hand and the seal of the <b>{county.upper()}</b> "
        f"District Land Registry this <b>{reg_date.day}</b> day of "
        f"<b>{reg_date.strftime('%B')}</b>, <b>{reg_date.year}</b>.",
        normal_style
    )

    right_block = [
        given_text,
        Spacer(1, 12),

        Paragraph(f"Name: <b>{registrar_name}</b>", normal_style),
        Spacer(1, 4),
        Paragraph("Stamp No.: _______________________", normal_style),
        Spacer(1, 4),
        Paragraph("Signature: _______________________", normal_style),
        Spacer(1, 6),
        Paragraph("<i>Land Registrar</i>", small_center)
    ]


    table = Table([[seal, right_block]], colWidths=[180, 330])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, -1), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))


    elements.append(Paragraph(
        "<b>Official Land Title Deed – TitleGuard System</b>",
        small_center
    ))


    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"deed_{land_record.land_records_parcel_number}.pdf\"'
    return response


# ===================== LAND RECORDS REPORT DOWNLOAD =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_land_records_report(request):
    """
    Download Land Records Report
    """
    
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        user = request.user

        county_filter = request.GET.get('county', '')
        
        if user.user_role == 'user':
            land_records = LandRecord.objects.filter(land_records_owner_id=user)
            land_records = land_records.exclude(
            land_records_verification_status__in=['flagged', 'rejected', 'transferred'])
        elif user.user_role in ['land_officer', 'legal_officer']:
            if user.user_county:
                land_records = LandRecord.objects.filter(land_records_county__iexact=user.user_county)  
            else:
                land_records = LandRecord.objects.none()
        else:
            if county_filter and county_filter != 'all':
                land_records = LandRecord.objects.filter(land_records_county__iexact=county_filter)
            else:
                land_records = LandRecord.objects.all().select_related('land_records_owner_id')

        search_term = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')

        if search_term:
            land_records = land_records.filter(
                Q(land_records_parcel_number__icontains=search_term) |
                Q(land_records_deed_number__icontains=search_term) |
                Q(land_records_location__icontains=search_term) |
                Q(land_records_owner_id__user_full_name__icontains=search_term)
            )
            
        if status_filter and status_filter != 'all':
            land_records = land_records.filter(land_records_verification_status=status_filter)

        buffer = BytesIO()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="land-records-report-{datetime.now().strftime("%Y-%m-%d")}.pdf"'

        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            "TitleGuardTitle",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=colors.HexColor("#1e7e34"),
            spaceAfter=20,
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
            alignment=1,
        )
        normal_style = styles["Normal"]
        normal_style.fontSize = 10
        normal_style.leading = 13

        elements.append(Paragraph("TITLEGUARD LAND MANAGEMENT SYSTEM", title_style))
        elements.append(Paragraph("LAND RECORDS REPORT", subtitle_style))
        elements.append(Spacer(1, 0.3 * inch))


        elements.append(Paragraph(f"Generated by: {user.user_full_name} ({user.user_role.replace('_', ' ').title()})", normal_style))
        elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
        
        if search_term:
            elements.append(Paragraph(f"Search Filter: {search_term}", normal_style))
        if status_filter and status_filter != 'all':
            elements.append(Paragraph(f"Status Filter: {status_filter}", normal_style))
            
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Spacer(1, 0.3 * inch))

        if land_records.exists():
            data = [["Parcel No.", "Deed No.", "Owner Name", "ID No.", "Location", "Size (Ha)", "Status", "Registered Date"]]

            for record in land_records:
                deed_number = record.land_records_deed_number
                if deed_number and len(deed_number) > 20:
                    deed_display = deed_number[:20] + "\n" + deed_number[20:40] + ("\n" + deed_number[40:60] if len(deed_number) > 40 else "")
                else:
                    deed_display = deed_number or "N/A"
                
                data.append([
                    record.land_records_parcel_number,
                    deed_display, 
                    record.land_records_owner_id.user_full_name if record.land_records_owner_id else "Unknown",
                    record.land_records_owner_id.user_id_number if record.land_records_owner_id else "Unknown",
                    record.land_records_location,
                    str(record.land_records_size),
                    record.land_records_verification_status.upper(),
                    record.land_records_first_registration_date.strftime("%Y-%m-%d"),
                ])

            
            table = Table(data, colWidths=[
                2.0*inch, 
                2.0*inch,  
                1.5*inch, 
                1.0*inch,  
                2.0*inch, 
                0.8*inch,  
                0.9*inch,  
                1.2*inch, 
            ])
            
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 6),   
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))


            elements.append(table)
        
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph(f"Total Records: {land_records.count()}", normal_style))
            
        else:
            elements.append(Paragraph("No land records found matching the specified criteria.", normal_style))

        elements.append(Spacer(1, 0.4 * inch))


        footer_text = f"""
        <para align=center>
        <b>TitleGuard Land Management System</b><br/>
        Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        </para>
        """
        elements.append(Paragraph(footer_text, normal_style))

        doc.build(elements)
        buffer.seek(0)
        response.write(buffer.read())
        
        return response
        
    except Exception as e:
        print(f"ERROR in download_land_records_report: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to generate land records report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
# ===================== DOCUMENTS =====================
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related(
        'document_land_records_id',
        'document_uploaded_by'
    ).all()

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['document_file_name', 'document_land_records_id__land_records_parcel_number']
    ordering_fields = ['document_created_at', 'document_status']
    ordering = ['-document_created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        user_profile = self.request.user

        if user_profile.role == 'user':
            queryset = queryset.filter(document_uploaded_by=user_profile)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(document_status=status_filter)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        document = serializer.save(
            document_uploaded_by=user,
            document_status='pending_payment'
        )

        Notification.objects.create(
            notification_user_id=user,
            notification_title='Payment Required',
            notification_message=f'Payment is required to verify your document "{document.document_file_name}".',
            notification_type='warning',
            notification_related_entity_type='document',
            notification_related_entity_id=document.document_id
        )


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def link_to_land_record(self, request, pk=None):
        """
        Link document to land record after OCR extraction
        """
        document = self.get_object()
        parcel_number = request.data.get('parcel_number')
        
        if not parcel_number:
            return Response(
                {'error': 'Parcel number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            land_record = LandRecord.objects.get(land_records_parcel_number=parcel_number)
            document.document_land_records_id = land_record
            document.save()
            
            serializer = self.get_serializer(document)
            return Response({
                'message': f'Document linked to land record {parcel_number}',
                'document': serializer.data
            })
            
        except LandRecord.DoesNotExist:
            return Response(
                {'error': f'Land record with parcel number {parcel_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )



    @action(detail=True, methods=['post'], permission_classes=[IsLandOfficer])
    def verify(self, request, pk=None):
        document = self.get_object()
        serializer = DocumentVerificationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        document.document_authenticity_score = serializer.validated_data['authenticity_score']
        document.document_verification_notes = serializer.validated_data.get('verification_notes', '')
        document.document_status = serializer.validated_data['status']
        document.document_verified_by = request.user
        document.document_verified_at = timezone.now()
        document.save()

        Notification.objects.create(
            notification_user_id=document.document_uploaded_by,
            notification_title=f'Document {document.document_status.capitalize()}',
            notification_message=f'Your document "{document.document_file_name}" has been {document.document_status}.',
            notification_type='success' if document.document_status == 'verified' else 'error',
            notification_related_entity_type='document',
            notification_related_entity_id=document.document_id
        )

        response_serializer = DocumentDetailSerializer(document)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'])
    def process_ocr(self, request, pk=None):
        document = self.get_object()
        if document.document_status != 'pending':
            return Response({'error': 'Document has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = process_ocr(document)
            document.document_status = 'processing'
            document.save()
            return Response({'message': 'OCR processing started', 'document_id': str(document.document_id)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# ===================== TRANSACTIONS =====================
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related(
        'transaction_land_record_id', 
        'transaction_from_owner_id', 
        'transaction_to_owner_id',
        'transaction_legal_officer_id',
        'transaction_land_officer_id'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'transaction_land_record_id__land_records_parcel_number', 
        'transaction_payment_reference',
        'transaction_from_owner_id__user_full_name',
        'transaction_to_owner_id__user_full_name'
    ]
    ordering_fields = [
        'transaction_created_at', 
        'transaction_amount', 
        'transaction_legal_approval_status'
    ]
    ordering = ['-transaction_created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'create':
            return TransactionCreateSerializer
        return TransactionDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user


        if user.user_role == 'user':
            queryset = queryset.filter(
                Q(transaction_from_owner_id=user) | 
                Q(transaction_to_owner_id=user)
            )


        elif user.user_role == 'legal_officer':
            queryset = queryset.filter(
                transaction_county__iexact=user.user_county
            )

        elif user.user_role == 'land_officer':
            queryset = queryset.filter(
                transaction_county__iexact=user.user_county
            )



        elif user.user_role in ['admin', 'superadmin']:
            queryset = queryset.all()

        approval_status = self.request.query_params.get('approval_status')
        if approval_status:
            queryset = queryset.filter(transaction_legal_approval_status=approval_status)


        county_filter = self.request.query_params.get('county')
        if county_filter and user.user_role in ['admin', 'superadmin']:
            queryset = queryset.filter(transaction_county__iexact=county_filter) 

        return queryset


    @action(detail=True, methods=['post'], permission_classes=[IsLegalOfficer])
    def approve_legal(self, request, pk=None):
        try:
            transaction = self.get_object()
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        approval_status = request.data.get('status')
        legal_notes = request.data.get('legal_notes', '')

        if approval_status not in ['approved', 'rejected']:
            return Response(
                {'error': 'Invalid approval status. Must be "approved" or "rejected"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.transaction_legal_approval_status = approval_status
        transaction.transaction_legal_notes = legal_notes
        transaction.transaction_legal_officer_id = request.user
        transaction.transaction_approved_at = timezone.now()

        if approval_status == 'approved' and transaction.transaction_amount:
            transaction.legal_officer_commission = Decimal(transaction.transaction_amount) * Decimal('0.02')

            transaction.land_officer_commission = Decimal(transaction.transaction_amount) * Decimal('0.01')

        transaction.save()


        if transaction.transaction_from_owner_id:
            Notification.objects.create(
                notification_user_id=transaction.transaction_from_owner_id,
                notification_title=f'Transaction {approval_status.capitalize()}',
                notification_message=f'Transaction for {transaction.transaction_land_record_id.land_records_parcel_number} has been {approval_status} by legal officer.',
                notification_type='success' if approval_status == 'approved' else 'warning'
            )

        if approval_status == 'approved' and transaction.transaction_legal_officer_id:
            Notification.objects.create(
                notification_user_id=transaction.transaction_legal_officer_id,
                notification_title='Commission Earned',
                notification_message=f'You earned KES {transaction.legal_officer_commission:,.2f} for approving the transaction.',
                notification_type='success'
            )

        serializer = self.get_serializer(transaction)
        return Response(serializer.data)

# ===================== NOTIFICATIONS =====================
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('notification_user_id').all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-notification_created_at']

    def get_queryset(self):
        user_profile = self.request.user
        

        if user_profile.user_role in ['admin', 'superadmin']:
            return self.queryset.all()
        

        return self.queryset.filter(notification_user_id=user_profile)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        try:
            notification = self.get_object()
            
            if notification.notification_user_id != request.user and request.user.user_role not in ['admin', 'superadmin']:
                return Response(
                    {'error': 'You can only mark your own notifications as read'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            notification.notification_read = True
            notification.save()
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
            
        except Exception as e:
            print(f"Error marking notification as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark notification as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        try:
            user_profile = request.user
            
            updated_count = self.queryset.filter(
                notification_user_id=user_profile, 
                notification_read=False
            ).update(notification_read=True)
            
            return Response({
                'message': f'Marked {updated_count} notifications as read',
                'updated_count': updated_count
            })
            
        except Exception as e:
            print(f"Error marking all notifications as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark all notifications as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        try:
            user_profile = request.user
            
            if user_profile.user_role in ['admin', 'superadmin']:
                count = self.queryset.filter(notification_read=False).count()
            else:
                count = self.queryset.filter(
                    notification_user_id=user_profile, 
                    notification_read=False
                ).count()
            
            return Response({'unread_count': count})
            
        except Exception as e:
            print(f"Error getting unread count: {str(e)}")
            return Response({'unread_count': 0})

# ===================== DASHBOARD =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_statistics(request):
    user_profile = request.user
    role = user_profile.user_role
    

    stats = {
        "totalLandRecords": 0,
        "verifiedRecords": 0,
        "pendingVerifications": 0,
        "flaggedRecords": 0,
        "pendingLegalApprovals": 0,
        "recentTransactions": 0,
        "totalUsers": 0,
        "totalRevenue": 0,  
        "userPendingFees": 0,
        "userMoneyPaid": 0, 
        "countyRevenue": 0,  
        "countyTransactions": 0,
        
    }

    # === ADMIN / SUPERADMIN ===
    if role in ["admin", "superadmin"]:
        stats["totalLandRecords"] = LandRecord.objects.count()
        stats["verifiedRecords"] = LandRecord.objects.filter(land_records_verification_status="verified").count()
        stats["pendingVerifications"] = LandRecord.objects.filter(land_records_verification_status="pending").count()
        stats["flaggedRecords"] = LandRecord.objects.filter(land_records_verification_status="flagged").count()
        stats["pendingLegalApprovals"] = Transaction.objects.filter(transaction_legal_approval_status="pending").count()
        
        stats["recentTransactions"] = Transaction.objects.filter(
            transaction_created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        stats["totalUsers"] = UserProfile.objects.filter(user_is_registered=True).count()
        
        completed_transactions = Transaction.objects.filter(
            transaction_payment_status="completed"
        )
        stats["totalRevenue"] = float(sum(
            t.transaction_amount for t in completed_transactions 
            if t.transaction_amount
        ) or 0)
        stats["overall_legal_cases"] = LegalCaseSubmission.objects.count()
        stats["user_legal_cases"] = stats["overall_legal_cases"] 
        



    # === LAND OFFICER ===
    elif role == "land_officer":
        user_county = user_profile.user_county
        
        if user_county:
            county_land_records = LandRecord.objects.filter(land_records_county__iexact=user_county)
            stats["totalLandRecords"] = county_land_records.count()
            stats["verifiedRecords"] = county_land_records.filter(land_records_verification_status="verified").count()
            stats["pendingVerifications"] = county_land_records.filter(land_records_verification_status="pending").count()
            stats["flaggedRecords"] = county_land_records.filter(land_records_verification_status="flagged").count()
            
            county_transactions = Transaction.objects.filter(
                transaction_county__iexact=user_county
            )
            stats["recentTransactions"] = county_transactions.count()
            stats["pendingLegalApprovals"] = county_transactions.filter(
                transaction_legal_approval_status='pending'
            ).count()

            
            
            county_completed_transactions = Transaction.objects.filter(
                transaction_county__iexact=user_county,
                transaction_payment_status='completed'
            )

            stats["countyRevenue"] = float(
                county_completed_transactions.aggregate(
                    total=Sum('transaction_land_officer_share')
                )['total'] or 0
            )

            
            stats["totalRevenue"] = stats["countyRevenue"]
            stats["user_legal_cases"] = LegalCaseSubmission.objects.filter(
            case_land_record__land_records_county__iexact=user_county).count()

    # === LEGAL OFFICER ===
    elif role == "legal_officer":
        user_county = user_profile.user_county
        
        if user_county:
            stats["flaggedRecords"] = LandRecord.objects.filter(
                land_records_verification_status="flagged",
                land_records_county__iexact=user_county  
            ).count()
            
            
            county_transactions = Transaction.objects.filter(
                transaction_county__iexact=user_county
            )
            stats["recentTransactions"] = county_transactions.count()
            stats["pendingLegalApprovals"] = county_transactions.filter(
                transaction_legal_approval_status='pending'
            ).count()

            
            county_completed_transactions = Transaction.objects.filter(
                transaction_county__iexact=user_county,
                transaction_payment_status='completed',
                transaction_legal_approval_status='approved'
            )

            stats["countyRevenue"] = float(
                county_completed_transactions.aggregate(
                    total=Sum('transaction_legal_officer_share')
                )['total'] or 0
            )

            
            stats["totalRevenue"] = stats["countyRevenue"]
            stats["user_legal_cases"] = LegalCaseSubmission.objects.filter(
            case_land_record__land_records_county__iexact=user_county).count()
            

    # === NORMAL USER ===
    elif role == "user":
        stats["totalLandRecords"] = LandRecord.objects.filter(
            land_records_owner_id=user_profile
        ).exclude(land_records_verification_status__in=["flagged", "rejected"]).count()

        stats["verifiedRecords"] = LandRecord.objects.filter(
            land_records_owner_id=user_profile,
            land_records_verification_status="verified"
        ).count()

        stats["pendingVerifications"] = Document.objects.filter(
            document_uploaded_by=user_profile,
            document_status__in=["pending", "pending_payment"]
        ).count()
        
        stats["recentTransactions"] = Transaction.objects.filter(
            Q(transaction_from_owner_id=user_profile) |
            Q(transaction_to_owner_id=user_profile),
            transaction_created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        pending_fees = Transaction.objects.filter(
            transaction_from_owner_id=user_profile,
            transaction_payment_status="pending"
        )
        stats["userPendingFees"] = float(sum(
            t.transaction_amount for t in pending_fees 
            if t.transaction_amount
        ) or 0)
        
        completed_payments = Transaction.objects.filter(
            transaction_from_owner_id=user_profile,
            transaction_payment_status="completed"
        )
        stats["userMoneyPaid"] = float(sum(
            t.transaction_amount for t in completed_payments 
            if t.transaction_amount
        ) or 0)
        
        stats["totalRevenue"] = stats["userMoneyPaid"]

    return Response(stats)

UserProfile = get_user_model()

# ===============================================
#  ADMIN ADD USERS 
# ===============================================
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd

class AdminAddMinimalUsersView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        admin = request.user
        if admin.user_role not in ['admin', 'superadmin']:
            return Response({'error': 'Only admin can perform this action'}, status=403)

        full_name = request.data.get('full_name')
        id_number = request.data.get('id_number')
        file = request.FILES.get('file')

        # --- SINGLE ENTRY ---
        if full_name and id_number and not file:
            id_number = str(id_number).strip()
            if UserProfile.objects.filter(user_id_number__iexact=id_number).exists():
                return Response({'error': 'User with this ID number already exists'}, status=400)

            placeholder_email = f"pending_{id_number}@titleguard.local"
            UserProfile.objects.create(
                user_full_name=full_name.strip(),
                user_id_number=id_number,
                user_role='user',
                user_is_registered=False,
                user_email=placeholder_email
            )
            return Response({'message': 'Minimal user added successfully'}, status=201)

        # --- BULK UPLOAD (CSV/EXCEL) ---
        if file:
            try:
                fname = file.name.lower()
                if fname.endswith('.csv'):
                    df = pd.read_csv(file, dtype=str)
                elif fname.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file, dtype=str)
                else:
                    return Response({'error': 'Upload only CSV or Excel files'}, status=400)

                added = 0
                for _, row in df.iterrows():
                    name = (row.get('full_name') or row.get('name') or '').strip()
                    id_no = (row.get('id_number') or row.get('id') or '').strip()
                    if not name or not id_no:
                        continue
                    if UserProfile.objects.filter(user_id_number__iexact=id_no).exists():
                        continue

                    placeholder_email = f"pending_{id_no}@titleguard.local"
                    UserProfile.objects.create(
                        user_full_name=name,
                        user_id_number=id_no,
                        user_role='user',
                        user_is_registered=False,
                        user_email=placeholder_email
                    )
                    added += 1

                return Response({'message': f'{added} users added successfully'}, status=201)
            except Exception as e:
                return Response({'error': str(e)}, status=400)

        return Response({'error': 'Provide full_name + id_number or upload a CSV/Excel file'}, status=400)


class Command(BaseCommand):
    help = 'Ensure each county has one land officer and one legal officer'

    def handle(self, *args, **options):
        counties = [choice[0] for choice in UserProfile.COUNTY_CHOICES]
        
        for county in counties:
            land_officers = UserProfile.objects.filter(
                user_role='land_officer',
                user_county=county,
                user_is_active=True
            )
            
            if land_officers.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'❌ No land officer assigned to {county}')
                )
            elif land_officers.count() > 1:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Multiple land officers in {county}: {land_officers.count()}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Land officer assigned to {county}')
                )
            
            legal_officers = UserProfile.objects.filter(
                user_role='legal_officer',
                user_county=county,
                user_is_active=True
            )
            
            if legal_officers.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'❌ No legal officer assigned to {county}')
                )
            elif legal_officers.count() > 1:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Multiple legal officers in {county}: {legal_officers.count()}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Legal officer assigned to {county}')
                )
            
            self.stdout.write('---')

# ===================== OCR & PAYMENTS =====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_ocr_endpoint(request):
    """
    Trigger OCR verification for a document after payment.
    """
    document_id = request.data.get('document_id')
    if not document_id:
        return Response({'error': 'document_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    if document.status != 'pending':
        return Response({'error': 'Document has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = process_ocr(document)
        document.status = 'processing'
        document.save()
        return Response({
            'message': 'OCR processing started',
            'document_id': str(document.id),
            'metadata': result.get('metadata', {}),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_verification(request, document_id):
    try:
        document = Document.objects.get(document_id=document_id)
        doc_name = document.document_file_name

        document.delete()
        return Response(
            {"message": f"Verification '{doc_name}' deleted successfully."},
            status=status.HTTP_200_OK
        )
    except Document.DoesNotExist:
        return Response(
            {"error": "Document not found."},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_transfer_payment(request):
    user = request.user
    land_record_id = request.data.get('land_record_id')
    to_owner_id_number = request.data.get('to_owner_id_number')
    amount = request.data.get('amount')
    phone_number = request.data.get('phone_number')
    transaction_type = request.data.get('transaction_type', 'transfer')

    if not all([land_record_id, to_owner_id_number, amount, phone_number]):
        return Response({'error': 'Missing required fields'}, status=400)

    try:
        land_record = LandRecord.objects.get(land_records_id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response({'error': 'Invalid land record ID'}, status=404)

    if land_record.land_records_owner_id != user:
        return Response({'error': 'You can only transfer land that you own'}, status=403)


    try:
        to_owner_profile = UserProfile.objects.get(user_id_number=to_owner_id_number)
    except UserProfile.DoesNotExist:
        return Response({
            'error': 'User with this ID number not found in the system',
            'id_number': to_owner_id_number
        }, status=404)

    from_owner_profile = user

    
    transaction_county = land_record.land_records_county

    if phone_number.startswith(("0712", "0799", "0700", "0740")):
        fake_checkout = f"SIMULATED_{random.randint(1000,9999)}"

        print(f" Simulating payment success - AUTO-COMPLETING TRANSFER to ID: {to_owner_id_number}")

        transaction = Transaction.objects.create(
            transaction_land_record_id=land_record,
            transaction_from_owner_id=from_owner_profile,
            transaction_to_owner_id_number=to_owner_id_number,
            transaction_to_owner_id=to_owner_profile,
            transaction_type=transaction_type,
            transaction_amount=amount,
            transaction_county=transaction_county,  
            transaction_payment_reference=fake_checkout,
            transaction_payment_status='completed',
            transaction_legal_approval_status='approved',
            transaction_approved_at=timezone.now(),
            transaction_legal_officer_share=Decimal('350.00'),
            transaction_land_officer_share=Decimal('650.00')
        )

        transaction.assign_officers_by_county()

        new_deed_number = land_record.transfer_ownership(to_owner_profile, transaction)
        
        transaction.transaction_transfer_completed = True
        transaction.transaction_new_deed_number = new_deed_number
        transaction.save()

        Notification.objects.create(
            notification_user_id=from_owner_profile,
            notification_title='Transfer Completed',
            notification_message=f'Transfer of {land_record.land_records_parcel_number} to {to_owner_profile.user_full_name} has been completed successfully. New deed: {new_deed_number}',
            notification_type='success'
        )

        Notification.objects.create(
            notification_user_id=to_owner_profile,
            notification_title='New Property Received',
            notification_message=f'You are now the official owner of {land_record.land_records_parcel_number}. New deed number: {new_deed_number}',
            notification_type='success'
        )


        return Response({
            'success': True,
            'checkout_request_id': fake_checkout,
            'message': f'Payment successful and transfer completed to {to_owner_profile.user_full_name}.',
            'transaction_id': str(transaction.transaction_id),
            'new_deed_number': new_deed_number,
            'to_owner_name': to_owner_profile.user_full_name
        }, status=200)

    # REAL M-PESA 
    from .mpesa_service import MpesaService
    mpesa = MpesaService()

    stk_response = mpesa.initiate_stk_push(
        phone_number,
        amount,
        f"Transfer-{land_record.land_records_parcel_number}",
        f"Land transfer to ID: {to_owner_id_number}"
    )

    if not stk_response.get('CheckoutRequestID'):
        return Response({'error': 'Failed to initiate payment'}, status=400)

    transaction = Transaction.objects.create(
        transaction_land_record_id=land_record,
        transaction_from_owner_id=from_owner_profile,
        transaction_to_owner_id_number=to_owner_id_number,
        transaction_to_owner_id=to_owner_profile,
        transaction_type=transaction_type,
        transaction_amount=amount,
        transaction_county=transaction_county, 
        transaction_payment_reference=stk_response['CheckoutRequestID'],
        transaction_payment_status='pending'
    )

    transaction.assign_officers_by_county()

    Notification.objects.create(
        notification_user_id=from_owner_profile,
        notification_title='Payment Initiated',
        notification_message=f'Payment initiated for transfer of {land_record.land_records_parcel_number} to {to_owner_profile.user_full_name}.',
        notification_type='info'
    )

    return Response({
        'success': True,
        'checkout_request_id': stk_response['CheckoutRequestID'],
        'message': f'Payment initiated successfully. Transfer will auto-complete to {to_owner_profile.user_full_name}.',
        'to_owner_name': to_owner_profile.user_full_name
    }, status=200)


    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request, checkout_id):
    """
    Check transaction status (works for both simulated and real M-PESA).
    """
    from .models import Transaction
    from django.db.models import Q

    try:
        transaction = Transaction.objects.filter(
            Q(transaction_payment_reference__icontains=checkout_id)
        ).order_by('-created_at').first()

        if not transaction:
            return Response({'status': 'not_found'}, status=404)


        return Response({
            'status': transaction.transaction_payment_status,
            'amount': transaction.transaction_amount,
            'reference': transaction.transaction_payment_reference,
        }, status=200)

    except Exception as e:
        return Response({'status': 'error', 'error': str(e)}, status=500)


# ===================== TRANSFER INITIATION =====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_transfer(request):
    land_record_id = request.data.get('land_record_id')
    to_owner_email = request.data.get('to_owner_email')
    transaction_type = request.data.get('transaction_type', 'transfer')
    amount = request.data.get('amount')
    payment_reference = request.data.get('payment_reference')

    if not land_record_id or not to_owner_email:
        return Response(
            {'error': 'Land record ID and new owner email are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        land_record = LandRecord.objects.get(id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response(
            {'error': 'Land record not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if land_record.owner != request.user:
        return Response(
            {'error': 'You can only transfer land that you own'},
            status=status.HTTP_403_FORBIDDEN
        )

    if land_record.has_legal_case or land_record.verification_status == 'flagged':
        return Response(
            {
                'error': 'Cannot transfer flagged property',
                'message': 'This land has an active legal case and cannot be transferred until resolved.',
                'legal_case_description': land_record.legal_case_description
            },
            status=status.HTTP_400_BAD_REQUEST
        )


    try:
        to_owner = UserProfile.objects.get(email=to_owner_email, role='user')
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'New owner not found. They must be a registered user.'},
            status=status.HTTP_404_NOT_FOUND
        )


    if not payment_reference:
        return Response(
            {'error': 'Payment reference is required to initiate transfer'},
            status=status.HTTP_400_BAD_REQUEST
        )


    transaction = Transaction.objects.create(
        land_record=land_record,
        from_owner=request.user,
        to_owner=to_owner,
        transaction_type=transaction_type,
        amount=amount,
        payment_reference=payment_reference,
        payment_status='completed',
        legal_approval_status='pending',
        transfer_accepted=False
    )


    transaction.generate_acceptance_token()

    Notification.objects.create(
        notification_user=request.user,
        notification_title='Transfer Initiated',
        notification_message=f'Transfer request sent for {land_record.parcel_number} to {to_owner.full_name}. Awaiting acceptance.',
        notification_type='info',
        notification_related_entity_type='transaction',
        notification_related_entity_id=transaction.id
    )

    Notification.objects.create(
        notification_user=to_owner,
        notification_title='Transfer Request Received',
        notification_message=f'You have received a land transfer request for {land_record.parcel_number}. Check your email to accept or reject.',
        notification_type='warning',
        notification_related_entity_type='transaction',
        notification_related_entity_id=transaction.id
    )

    serializer = TransactionDetailSerializer(transaction)
    return Response({
        'message': 'Transfer initiated successfully. Awaiting new owner acceptance.',
        'transaction': serializer.data
    }, status=status.HTTP_201_CREATED)


# ===================== ACCEPT/REJECT TRANSFER =====================
@api_view(['POST'])
@permission_classes([AllowAny])
def accept_transfer(request, token):
    try:
        transaction = Transaction.objects.get(transfer_acceptance_token=token)
    except Transaction.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired transfer link'},
            status=status.HTTP_404_NOT_FOUND
        )

    if timezone.now() > transaction.transfer_acceptance_expires_at:
        transaction.legal_approval_status = 'rejected'
        transaction.save()
        return Response(
            {'error': 'Transfer link has expired'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if transaction.transfer_accepted:
        return Response(
            {'error': 'Transfer already accepted'},
            status=status.HTTP_400_BAD_REQUEST
        )

    action = request.data.get('action')  

    if action == 'accept':
        transaction.transfer_accepted = True
        transaction.save()

        Notification.objects.create(
            user=transaction.from_owner,
            title='Transfer Accepted',
            message=f'{transaction.to_owner.full_name} has accepted the transfer for {transaction.land_record.parcel_number}. Awaiting legal approval.',
            type='success',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

        Notification.objects.create(
            user=transaction.to_owner,
            title='Transfer Accepted',
            message=f'You accepted the transfer for {transaction.land_record.parcel_number}. Legal review is in progress.',
            type='success',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

        return Response({
            'message': 'Transfer accepted successfully. Awaiting legal officer approval.'
        })

    elif action == 'reject':
        transaction.legal_approval_status = 'rejected'
        transaction.save()


        Notification.objects.create(
            user=transaction.from_owner,
            title='Transfer Rejected',
            message=f'{transaction.to_owner.full_name} has rejected the transfer for {transaction.land_record.parcel_number}.',
            type='error',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

        return Response({
            'message': 'Transfer rejected successfully.'
        })

    else:
        return Response(
            {'error': 'Invalid action. Must be "accept" or "reject"'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ===================== LEGAL OFFICER APPROVAL =====================
@api_view(['POST'])
@permission_classes([IsLegalOfficer])
def approve_transfer(request, transaction_id):
    """
    Legal officer approves transfer and updates land record ownership
    """
    try:
        if isinstance(transaction_id, str):
            transaction_id = uuid.UUID(transaction_id)
        
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except (Transaction.DoesNotExist, ValueError):
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not transaction.transfer_accepted:
        return Response(
            {'error': 'Transfer must be accepted by new owner first'},
            status=status.HTTP_400_BAD_REQUEST
        )

    approval_status = request.data.get('status')  
    legal_notes = request.data.get('legal_notes', '')
    land_officer_id = request.data.get('land_officer_id')

    if approval_status not in ['approved', 'rejected']:
        return Response(
            {'error': 'Invalid approval status. Must be "approved" or "rejected"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    land_officer = None
    if approval_status == 'approved' and land_officer_id:
        try:
            land_officer = UserProfile.objects.get(user_id=land_officer_id, user_role='land_officer')
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Valid land officer must be assigned for approval'},
                status=status.HTTP_404_NOT_FOUND
            )

    transaction.transaction_legal_approval_status = approval_status
    transaction.transaction_legal_notes = legal_notes
    transaction.transaction_legal_officer_id = request.user
    
    if land_officer:
        transaction.transaction_land_officer_id = land_officer
        
    transaction.transaction_approved_at = timezone.now()

    if approval_status == 'approved':
        transaction.transaction_legal_officer_share = Decimal('350.00')  
        transaction.transaction_land_officer_share = Decimal('650.00')  

        land_record = transaction.transaction_land_record_id
        
        old_deed_number = land_record.land_records_deed_number
        
        new_deed_number = land_record.transfer_ownership(
            transaction.transaction_to_owner_id, 
            transaction
        )
        

        transaction.transaction_transfer_completed = True
        transaction.transaction_new_deed_number = new_deed_number

    transaction.save()

    if approval_status == 'approved':
        Notification.objects.create(
            notification_user_id=transaction.transaction_from_owner_id,
            notification_title='Transfer Completed',
            notification_message=f'Transfer of {land_record.land_records_parcel_number} to {transaction.transaction_to_owner_id.user_full_name} has been completed. New deed: {new_deed_number}',
            notification_type='success'
        )

        Notification.objects.create(
            notification_user_id=transaction.transaction_to_owner_id,
            notification_title='Ownership Transfer Complete',
            notification_message=f'You are now the official owner of {land_record.land_records_parcel_number}. New deed number: {new_deed_number}',
            notification_type='success'
        )

        Notification.objects.create(
            notification_user_id=request.user,
            notification_title='Commission Earned',
            notification_message=f'You earned KES 350 for approving transfer of {land_record.land_records_parcel_number}.',
            notification_type='success'
        )

        if land_officer:
            Notification.objects.create(
                notification_user_id=land_officer,
                notification_title='Commission Earned',
                notification_message=f'You earned KES 650 for processing transfer of {land_record.land_records_parcel_number}.',
                notification_type='success'
            )
    else:
        Notification.objects.create(
            notification_user_id=transaction.transaction_from_owner_id,
            notification_title='Transfer Rejected',
            notification_message=f'Transfer of {transaction.transaction_land_record_id.land_records_parcel_number} was rejected by legal officer.',
            notification_type='error'
        )

        Notification.objects.create(
            notification_user_id=transaction.transaction_to_owner_id,
            notification_title='Transfer Rejected',
            notification_message=f'Transfer of {transaction.transaction_land_record_id.land_records_parcel_number} was rejected by legal officer.',
            notification_type='error'
        )

    serializer = TransactionDetailSerializer(transaction)
    return Response({
        'message': f'Transfer {approval_status} successfully',
        'transaction': serializer.data
    })

# ===================== FLAG LAND (LEGAL OFFICER) =====================
@api_view(['POST'])
@permission_classes([IsLegalOfficer])
def flag_land_for_case(request):
    """
    Legal officer flags land due to legal dispute
    """
    land_record_id = request.data.get('land_record_id')
    case_description = request.data.get('case_description')

    if not land_record_id or not case_description:
        return Response(
            {'error': 'Land record ID and case description are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        land_record = LandRecord.objects.get(id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response(
            {'error': 'Land record not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    land_record.has_legal_case = True
    land_record.legal_case_description = case_description
    land_record.verification_status = 'flagged'
    land_record.save()

    Notification.objects.create(
        notification_user=land_record.owner,
        notification_title='Land Flagged - Legal Case',
        notification_message=f'Your land {land_record.parcel_number} has been flagged due to a legal case. Transfers are suspended.',
        notification_type='error',
        notification_related_entity_type='land_record',
        notification_related_entity_id=land_record.id
    )

    return Response({
        'message': 'Land flagged successfully',
        'land_record': {
            'id': str(land_record.id),
            'parcel_number': land_record.parcel_number,
            'has_legal_case': land_record.has_legal_case,
            'legal_case_description': land_record.legal_case_description
        }
    })


@api_view(['POST'])
@permission_classes([IsLegalOfficer])
def unflag_land(request):
    """
    Legal officer removes flag after case is resolved
    """
    land_record_id = request.data.get('land_record_id')

    try:
        land_record = LandRecord.objects.get(id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response(
            {'error': 'Land record not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    land_record.has_legal_case = False
    land_record.legal_case_description = None
    land_record.verification_status = 'verified'
    land_record.save()


    Notification.objects.create(
        notification_user=land_record.owner,
        notification_title='Land Unflagged',
        notification_message=f'The legal case for your land {land_record.parcel_number} has been resolved. You can now transfer it.',
        notification_type='success',
        notification_related_entity_type='land_record',
        notification_related_entity_id=land_record.id
    )

    return Response({
        'message': 'Land unflagged successfully'
    })


# ===================== VERIFICATION REQUEST  =====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_land_verification(request):
    land_record_id = request.data.get('land_record_id')
    payment_reference = request.data.get('payment_reference')

    if not land_record_id or not payment_reference:
        return Response(
            {'error': 'Land record ID and payment reference are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        land_record = LandRecord.objects.get(id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response(
            {'error': 'Land record not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    verification_request = VerificationRequest.objects.create(
        requested_by=request.user,
        land_record=land_record,
        payment_reference=payment_reference,
        payment_completed=True,
        status='completed',
        verification_summary=f"""
        Parcel Number: {land_record.parcel_number}
        Location: {land_record.location}
        Size: {land_record.size_hectares} hectares
        Status: {land_record.verification_status}
        Legal Case: {'Yes - Contact legal officer' if land_record.has_legal_case else 'No'}
        
        Note: Full owner details and documents are restricted. Contact land office for complete records.
        """
    )

    Notification.objects.create(
        user=request.user,
        title='Verification Complete',
        message=f'Verification details for {land_record.parcel_number} are now available.',
        type='success',
        related_entity_type='verification_request',
        related_entity_id=verification_request.id
    )

    serializer = VerificationRequestSerializer(verification_request)
    return Response({
        'message': 'Verification completed successfully',
        'verification': serializer.data
    })



# ===================== OFFICER COMMISSION REPORTS =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_commissions(request):
    user = request.user

    period = request.GET.get('period', 'all_time')
    county_filter = request.GET.get('county')

    now = timezone.now()
    start_date = None
    end_date = None

    if period == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif period == 'last_month':
        first_day_this_month = now.replace(day=1)
        start_date = (first_day_this_month - timedelta(days=1)).replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)

    # ==================== ADMIN VIEW  ====================
    if user.user_role == 'admin':

        base_query = Transaction.objects.filter(
            transaction_payment_status='completed'
        )

        if county_filter and county_filter != 'all':
            base_query = base_query.filter(transaction_county__iexact=county_filter)

        if start_date and end_date:
            base_query = base_query.filter(transaction_created_at__range=[start_date, end_date])
        elif start_date:
            base_query = base_query.filter(transaction_created_at__gte=start_date)

        transactions = base_query.select_related(
            'transaction_land_record_id',
            'transaction_land_record_id__land_records_owner_id',
            'transaction_legal_officer_id',
            'transaction_land_officer_id'
        ).order_by('-transaction_created_at')

        verification_revenue = 0
        legal_commissions = 0
        land_commissions = 0
        commission_transactions = []

        for t in transactions:
            county = t.transaction_county
            parcel = location = 'N/A'

            if t.transaction_land_record_id:
                parcel = t.transaction_land_record_id.land_records_parcel_number
                location = t.transaction_land_record_id.land_records_location
                county = t.transaction_land_record_id.land_records_county

            if t.transaction_type == 'verification':
                amount = float(t.transaction_amount or 0)
                verification_revenue += amount
                legal_share = land_share = 0
            else:
                legal_share = float(t.transaction_legal_officer_share or 0)
                land_share = float(t.transaction_land_officer_share or 0)
                legal_commissions += legal_share
                land_commissions += land_share
                amount = float(t.transaction_amount or 0)

            commission_transactions.append({
                'id': str(t.transaction_id),
                'transaction_id': str(t.transaction_id),
                'type': t.transaction_type,
                'land_record': {
                    'land_records_parcel_number': parcel,
                    'land_records_location': location,
                    'land_records_county': county,
                },
                'transaction_amount': amount,
                'transaction_legal_officer_share': legal_share,
                'transaction_land_officer_share': land_share,
                'transaction_created_at': t.transaction_created_at,
                'transaction_approved_at': t.transaction_approved_at,
                'transaction_payment_status': t.transaction_payment_status,
                'transaction_legal_approval_status': t.transaction_legal_approval_status,
                'legal_officer_name': t.transaction_legal_officer_id.user_full_name if t.transaction_legal_officer_id else 'N/A',
                'land_officer_name': t.transaction_land_officer_id.user_full_name if t.transaction_land_officer_id else 'N/A',
                'county': county,
            })

        return Response({
            'total_earnings': verification_revenue + legal_commissions + land_commissions,
            'verification_revenue': verification_revenue,
            'legal_commissions': legal_commissions,
            'land_commissions': land_commissions,
            'officer_commissions': legal_commissions + land_commissions,
            'transaction_count': len(commission_transactions),
            'commission_transactions': commission_transactions,
            'period': period,
        })

    # ==================== LEGAL OFFICER VIEW ====================
    elif user.user_role == 'legal_officer':

        base_query = Transaction.objects.filter(
            transaction_payment_status='completed',
            transaction_legal_approval_status='approved',
            transaction_county__iexact=user.user_county
        ).exclude(transaction_type='verification')

        if start_date and end_date:
            base_query = base_query.filter(transaction_approved_at__range=[start_date, end_date])
        elif start_date:
            base_query = base_query.filter(transaction_approved_at__gte=start_date)

        transactions = base_query.select_related(
            'transaction_land_record_id'
        ).order_by('-transaction_approved_at')

        total_earnings = 0
        commission_transactions = []

        for t in transactions:
            commission = float(t.transaction_legal_officer_share or 0)
            total_earnings += commission

            parcel = location = 'N/A'
            county = t.transaction_county

            if t.transaction_land_record_id:
                parcel = t.transaction_land_record_id.land_records_parcel_number
                location = t.transaction_land_record_id.land_records_location
                county = t.transaction_land_record_id.land_records_county

            commission_transactions.append({
                'id': str(t.transaction_id),
                'transaction_id': str(t.transaction_id),
                'type': t.transaction_type,
                'land_record': {
                    'land_records_parcel_number': parcel,
                    'land_records_location': location,
                    'land_records_county': county,
                },
                'transaction_amount': float(t.transaction_amount or 0),
                'your_commission': commission,
                'transaction_created_at': t.transaction_created_at,
                'transaction_approved_at': t.transaction_approved_at,
                'transaction_payment_status': t.transaction_payment_status,
                'transaction_legal_approval_status': 'approved',
                'county': county,
            })

        return Response({
            'total_earnings': total_earnings,
            'transaction_count': len(commission_transactions),
            'commission_transactions': commission_transactions,
            'user_county': user.user_county,
            'period': period,
        })

    # ==================== LAND OFFICER VIEW ====================
    elif user.user_role == 'land_officer':

        base_query = Transaction.objects.filter(
            transaction_payment_status='completed',
            transaction_county__iexact=user.user_county
        ).exclude(transaction_type='verification')

        if start_date and end_date:
            base_query = base_query.filter(transaction_approved_at__range=[start_date, end_date])
        elif start_date:
            base_query = base_query.filter(transaction_approved_at__gte=start_date)

        transactions = base_query.select_related(
            'transaction_land_record_id'
        ).order_by('-transaction_approved_at')

        total_earnings = 0
        commission_transactions = []

        for t in transactions:
            commission = float(t.transaction_land_officer_share or 0)
            total_earnings += commission

            parcel = location = 'N/A'
            county = t.transaction_county

            if t.transaction_land_record_id:
                parcel = t.transaction_land_record_id.land_records_parcel_number
                location = t.transaction_land_record_id.land_records_location
                county = t.transaction_land_record_id.land_records_county

            commission_transactions.append({
                'id': str(t.transaction_id),
                'transaction_id': str(t.transaction_id),
                'type': t.transaction_type,
                'land_record': {
                    'land_records_parcel_number': parcel,
                    'land_records_location': location,
                    'land_records_county': county,
                },
                'transaction_amount': float(t.transaction_amount or 0),
                'your_commission': commission,
                'transaction_created_at': t.transaction_created_at,
                'transaction_approved_at': t.transaction_approved_at,
                'transaction_payment_status': 'completed',
                'transaction_legal_approval_status': 'approved',
                'county': county,
            })

        return Response({
            'total_earnings': total_earnings,
            'transaction_count': len(commission_transactions),
            'commission_transactions': commission_transactions,
            'user_county': user.user_county,
            'period': period,
        })

    return Response(
        {'error': 'Only officers and administrators can view commissions'},
        status=403
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def county_revenue(request):
    """
    Get revenue statistics for a specific county.
    Logic is COUNTY-FIRST and ROLE-AWARE.
    """
    user = request.user

    # ------------------ DETERMINE COUNTY ------------------
    if user.user_role == 'admin':
        county = request.GET.get('county')
        if not county:
            return Response(
                {'error': 'County parameter is required for admin'},
                status=400
            )
    elif user.user_role in ['land_officer', 'legal_officer']:
        county = user.user_county
        if not county:
            return Response(
                {'error': 'No county assigned to officer'},
                status=400
            )
    else:
        return Response(
            {'error': 'Only officers and admins can view revenue'},
            status=403
        )

   
    base_query = Transaction.objects.filter(
        transaction_county__iexact=county,
        transaction_payment_status='completed'
    )

 
    if user.user_role in ['admin', 'legal_officer']:
        base_query = base_query.filter(
            transaction_legal_approval_status='approved'
        )

    transactions = base_query.select_related(
        'transaction_land_record_id',
        'transaction_land_record_id__land_records_owner_id',
        'transaction_from_owner_id',
        'transaction_to_owner_id',
        'transaction_legal_officer_id',
        'transaction_land_officer_id'
    ).order_by('-transaction_created_at')


    total_earnings = 0
    commission_transactions = []

    for transaction in transactions:
        if user.user_role == 'admin':
            revenue_amount = float(transaction.transaction_amount or 0)

        elif user.user_role == 'legal_officer':
            revenue_amount = float(transaction.transaction_legal_officer_share or 0)

        else:  
            revenue_amount = float(transaction.transaction_land_officer_share or 0)

        total_earnings += revenue_amount

        parcel_number = 'N/A'
        location = 'N/A'
        land_county = county

        if transaction.transaction_land_record_id:
            parcel_number = transaction.transaction_land_record_id.land_records_parcel_number
            location = transaction.transaction_land_record_id.land_records_location
            land_county = transaction.transaction_land_record_id.land_records_county

        commission_transactions.append({
            'id': str(transaction.transaction_id),
            'transaction_id': str(transaction.transaction_id),
            'type': transaction.transaction_type,
            'land_record': {
                'land_records_id': (
                    str(transaction.transaction_land_record_id.land_records_id)
                    if transaction.transaction_land_record_id else None
                ),
                'land_records_parcel_number': parcel_number,
                'land_records_location': location,
                'land_records_county': land_county,
            },
            'transaction_amount': float(transaction.transaction_amount or 0),
            'revenue': revenue_amount,
            'transaction_legal_officer_share': float(transaction.transaction_legal_officer_share or 0),
            'transaction_land_officer_share': float(transaction.transaction_land_officer_share or 0),
            'transaction_created_at': transaction.transaction_created_at,
            'transaction_approved_at': transaction.transaction_approved_at,
            'transaction_legal_approval_status': transaction.transaction_legal_approval_status,
            'transaction_payment_status': transaction.transaction_payment_status,
            'legal_officer_name': (
                transaction.transaction_legal_officer_id.user_full_name
                if transaction.transaction_legal_officer_id else 'N/A'
            ),
            'land_officer_name': (
                transaction.transaction_land_officer_id.user_full_name
                if transaction.transaction_land_officer_id else 'N/A'
            ),
            'county': land_county,
        })


    return Response({
        'total_earnings': total_earnings,
        'transaction_count': len(commission_transactions),
        'transactions': commission_transactions,
        'county': county,
        'user_role': user.user_role,
    })

    
# ===================== DOCUMENT DOWNLOAD =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_document(request, document_id):
    try:
        document = Document.objects.select_related('land_record', 'uploaded_by').get(id=document_id)
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    user = request.user
    land_record = document.land_record

    can_download = False
    
    if land_record and land_record.owner == user:
        can_download = True
    
    elif user.role in ['land_officer', 'legal_officer', 'admin']:
        can_download = True
    
    elif document.uploaded_by == user:
        can_download = True

    if not can_download:
        return Response(
            {'error': 'You do not have permission to download this document'},
            status=status.HTTP_403_FORBIDDEN
        )

    if document.status == 'verified':
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e7e34'),
            spaceAfter=30,
            alignment=1  
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        normal_style.leading = 14


        elements.append(Paragraph("REPUBLIC OF KENYA", title_style))
        elements.append(Paragraph("LAND TITLE CERTIFICATE", header_style))
        elements.append(Spacer(1, 0.3*inch))


        details_data = [
            ['Document ID:', str(document.id)],
            ['Parcel Number:', land_record.parcel_number if land_record else 'N/A'],
            ['Deed Number:', land_record.deed_number if land_record else 'N/A'],
            ['Owner:', land_record.owner.full_name if land_record and land_record.owner else 'N/A'],
            ['Location:', land_record.location if land_record else 'N/A'],
            ['Size:', f"{land_record.size_hectares} hectares" if land_record else 'N/A'],
            ['Verification Status:', document.status.upper()],
            ['Verified By:', document.verified_by.full_name if document.verified_by else 'N/A'],
            ['Verification Date:', document.verified_at.strftime('%B %d, %Y') if document.verified_at else 'N/A'],
            ['Authenticity Score:', f"{document.authenticity_score}%" if document.authenticity_score else 'N/A'],
        ]

        table = Table(details_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))


        if document.verification_notes:
            elements.append(Paragraph("Verification Notes:", header_style))
            elements.append(Paragraph(document.verification_notes, normal_style))
            elements.append(Spacer(1, 0.2*inch))


        elements.append(Spacer(1, 0.5*inch))
        footer_text = f"""
        <para align=center>
        <b>This is a digitally verified document issued by TitleGuard Land Management System</b><br/>
        Document Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        </para>
        """
        elements.append(Paragraph(footer_text, normal_style))


        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="deed_{land_record.parcel_number if land_record else document_id}.pdf"'
        return response

    else:
        return Response(
            {'error': 'Only verified documents can be downloaded'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ===================== TRANSACTION RECEIPT DOWNLOAD =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_transaction_receipt(request, transaction_id):
    try:
        transaction = Transaction.objects.select_related(
            'land_record', 'from_owner', 'to_owner', 'legal_officer', 'land_officer'
        ).get(id=transaction_id)
    except Transaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    user = request.user


    can_download = False
    

    if user == transaction.from_owner or user == transaction.to_owner:
        can_download = True
    

    elif user == transaction.legal_officer or user == transaction.land_officer:
        can_download = True
    

    elif user.role in ['admin', 'land_officer', 'legal_officer']:
        can_download = True

    if not can_download:
        return Response(
            {'error': 'You do not have permission to download this transaction receipt'},
            status=status.HTTP_403_FORBIDDEN
        )


    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=1
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
    )


    elements.append(Paragraph("LAND OWNERSHIP TRANSFER RECEIPT", title_style))
    elements.append(Spacer(1, 0.2*inch))


    status_text = "APPROVED" if transaction.legal_approval_status == 'approved' else transaction.legal_approval_status.upper()
    status_color = colors.green if transaction.legal_approval_status == 'approved' else colors.orange
    
    elements.append(Paragraph(f"<b>Status:</b> <font color='{status_color.hexval()}'>{status_text}</font>", header_style))
    elements.append(Spacer(1, 0.2*inch))


    details_data = [
        ['Transaction ID:', str(transaction.id)],
        ['Transaction Type:', transaction.transaction_type.title()],
        ['Date:', transaction.created_at.strftime('%B %d, %Y')],
        ['', ''],
        ['PROPERTY DETAILS', ''],
        ['Parcel Number:', transaction.land_record.parcel_number],
        ['Deed Number:', transaction.land_record.deed_number],
        ['Location:', transaction.land_record.location],
        ['Size:', f"{transaction.land_record.size_hectares} hectares"],
        ['', ''],
        ['PARTIES INVOLVED', ''],
        ['Previous Owner:', transaction.from_owner.full_name if transaction.from_owner else 'N/A'],
        ['New Owner:', transaction.to_owner.full_name if transaction.to_owner else 'N/A'],
        ['', ''],
        ['PAYMENT DETAILS', ''],
        ['Amount:', f"KES {transaction.amount:,.2f}" if transaction.amount else 'N/A'],
        ['Payment Reference:', transaction.payment_reference or 'N/A'],
        ['Payment Status:', transaction.payment_status.title()],
        ['', ''],
        ['OFFICIAL VERIFICATION', ''],
        ['Legal Officer:', transaction.legal_officer.full_name if transaction.legal_officer else 'Pending'],
        ['Land Officer:', transaction.land_officer.full_name if transaction.land_officer else 'Pending'],
        ['Approval Date:', transaction.approved_at.strftime('%B %d, %Y') if transaction.approved_at else 'Pending'],
    ]

    table = Table(details_data, colWidths=[2.2*inch, 3.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 4), (1, 4), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 4), (1, 4), colors.white),
        ('BACKGROUND', (0, 10), (1, 10), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 10), (1, 10), colors.white),
        ('BACKGROUND', (0, 14), (1, 14), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 14), (1, 14), colors.white),
        ('BACKGROUND', (0, 18), (1, 18), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 18), (1, 18), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))


    if user.role in ['legal_officer', 'land_officer', 'admin']:
        elements.append(Paragraph("COMMISSION BREAKDOWN", header_style))
        commission_data = [
            ['Legal Officer Commission:', f"KES {transaction.legal_officer_commission:,.2f}" if transaction.legal_officer_commission else 'N/A'],
            ['Land Officer Commission:', f"KES {transaction.land_officer_commission:,.2f}" if transaction.land_officer_commission else 'N/A'],
        ]
        commission_table = Table(commission_data, colWidths=[2.2*inch, 3.8*inch])
        commission_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(commission_table)
        elements.append(Spacer(1, 0.3*inch))


    if transaction.legal_notes:
        elements.append(Paragraph("Legal Notes:", header_style))
        elements.append(Paragraph(transaction.legal_notes, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

 
    elements.append(Spacer(1, 0.4*inch))
    footer_text = f"""
    <para align=center>
    <b>Official Transaction Record - TitleGuard Land Management System</b><br/>
    Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    This document is legally binding and verifiable.<br/>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))


    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transaction_{transaction.land_record.parcel_number}_{transaction.created_at.strftime("%Y%m%d")}.pdf"'
    return response


# ===================== BULK DOWNLOAD (FOR OFFICERS) =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_my_transactions(request):
    """
    Officers can download all their transactions as a summary report
    """
    user = request.user

    if user.user_role not in ['legal_officer', 'land_officer']:
        return Response(
            {'error': 'Only officers can download transaction reports'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user.user_role == 'legal_officer':
        transactions = Transaction.objects.filter(
            transaction_legal_officer_id=user,
            transaction_legal_approval_status='approved'
        ).select_related(
            'transaction_land_record_id', 
            'transaction_from_owner_id', 
            'transaction_to_owner_id'
        )
        commission_field = 'legal_officer_commission'
        role_display = 'Legal Officer'
    else:
        transactions = Transaction.objects.filter(
            transaction_land_officer_id=user,
            transaction_legal_approval_status='approved'
        ).select_related(
            'transaction_land_record_id', 
            'transaction_from_owner_id', 
            'transaction_to_owner_id'
        )
        commission_field = 'land_officer_commission'
        role_display = 'Land Officer'


    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e7e34'),
        spaceAfter=20,
        alignment=1
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
    )


    elements.append(Paragraph("TITLEGUARD COMMISSION REPORT", title_style))
    elements.append(Spacer(1, 0.2*inch))

 
    total_transactions = transactions.count()
    total_earnings = sum(
        getattr(t, commission_field) or 0 for t in transactions
    )

    summary_data = [
        ['Officer Name:', user.user_full_name],
        ['Role:', role_display],
        ['Report Date:', datetime.now().strftime('%B %d, %Y')],
        ['Total Approved Transactions:', str(total_transactions)],
        ['Total Commission Earned:', f"KES {total_earnings:,.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("Transaction Details", header_style))
    elements.append(Spacer(1, 0.1*inch))


    if transactions.exists():
        trans_data = [['Date', 'Parcel No.', 'From Owner', 'To Owner', 'Amount', 'Commission']]
        
        for t in transactions:
            commission = getattr(t, commission_field) or 0
            trans_data.append([
                t.transaction_created_at.strftime('%Y-%m-%d'),
                t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else 'N/A',
                t.transaction_from_owner_id.user_full_name if t.transaction_from_owner_id else 'N/A',
                t.transaction_to_owner_id.user_full_name if t.transaction_to_owner_id else 'N/A',
                f"KES {t.transaction_amount:,.0f}" if t.transaction_amount else 'N/A',
                f"KES {commission:,.2f}"
            ])

        trans_table = Table(trans_data, colWidths=[1.0*inch, 1.2*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.3*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))

        elements.append(trans_table)
    else:
        elements.append(Paragraph("No commission transactions found.", styles['Normal']))


    elements.append(Spacer(1, 0.4*inch))
    footer_text = f"""
    <para align=center>
    <b>Official Commission Report - TitleGuard Land Management System</b><br/>
    Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    This document is for official use only.
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{user.user_role}_commission_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response


# ===================== USER REPORT WITH SUMMARY TABLE =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_user_report(request):
    buffer = BytesIO()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="user-management-report-{datetime.now().strftime("%Y-%m-%d")}.pdf"'

    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []


    title_style = ParagraphStyle(
        "TitleGuardTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e7e34"),
        spaceAfter=20,
        alignment=1, 
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=12,
        alignment=1,
    )

    normal_style = styles["Normal"]
    normal_style.fontSize = 10
    normal_style.leading = 13


    elements.append(Paragraph("TITLEGUARD LAND MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("USER MANAGEMENT REPORT", subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))



    elements.append(Paragraph("User Summary by Role", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))


    total_users = UserProfile.objects.filter(user_is_registered=True).count()
    admin_users = UserProfile.objects.filter(user_role__in=['admin', 'superadmin']).count()
    legal_officers = UserProfile.objects.filter(user_role='legal_officer').count()
    land_officers = UserProfile.objects.filter(user_role='land_officer').count()
    regular_users = UserProfile.objects.filter(user_role='user', user_is_registered=True).count()

    summary_data = [
        ["Role", "Count"],
        ["Total Users", str(total_users)],
        ["Administrators", str(admin_users)],
        ["Legal Officers", str(legal_officers)],
        ["Land Officers", str(land_officers)],
        ["Regular Users", str(regular_users)],
    ]

    summary_table = Table(summary_data, colWidths=[3.0*inch, 2.0*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),  
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.HexColor("#f8fdf8"),  
            colors.HexColor("#e8f5e8"),       
            colors.HexColor("#f8fdf8"),  
            colors.HexColor("#e8f5e8"),                
            colors.HexColor("#f8fdf8"),  
            colors.HexColor("#e8f5e8"),                
            colors.HexColor("#f8fdf8"),  
            colors.HexColor("#e8f5e8")           
        ]),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Detailed User List", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))

    users = UserProfile.objects.filter(user_is_registered=True).order_by("user_full_name")

    data = [
        [
            "Full Name",
            "Email Address",
            "Role",
            "Phone Number",
            "ID Number",
            "Created At",
        ]
    ]

    for user in users:
        role_display = user.user_role.replace('_', ' ').title()
        if user.user_role == 'user':
            role_display = 'Regular User'
        elif user.user_role in ['admin', 'superadmin']:
            role_display = 'Administrator'

        data.append([
            user.user_full_name,
            user.user_email,
            role_display,
            user.user_phone_number or "—",
            user.user_id_number or "—",
            user.user_created_at.strftime("%Y-%m-%d"),
        ])


    table = Table(
        data,
        colWidths=[2.0*inch, 2.8*inch, 1.3*inch, 1.5*inch, 1.2*inch, 1.5*inch]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),  # Header green
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

 
    footer_text = f"""
    <para align=center>
    <b>TitleGuard Land Management System</b><br/>
    Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    Total Users: {total_users} | Contact: titleguardadmin@gmail.com | +254 721 327 589
    </para>
    """
    elements.append(Paragraph(footer_text, normal_style))


    doc.build(elements)
    buffer.seek(0)
    response.write(buffer.read())

    return response

# ===================== COMMISSION REPORT =====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_commissions_report(request):
    user = request.user
    
    if user.user_role not in ['legal_officer', 'land_officer', 'admin']:
        return Response(
            {'error': 'Only officers and administrators can download commission reports'},
            status=status.HTTP_403_FORBIDDEN
        )

 
    county_filter = request.GET.get('county', user.user_county if user.user_role != 'admin' else None)
    period = request.GET.get('period', 'all_time')


    if user.user_role == 'legal_officer':
        user_role_display = "Legal Officer"
        commission_type = "Legal Commission"

        transactions = Transaction.objects.filter(
            transaction_payment_status='completed',
            transaction_legal_approval_status='approved',
            transaction_county__iexact=user.user_county
        ).exclude(transaction_type='verification')
        

        if user.user_county:
            county_transactions = Transaction.objects.filter(
                transaction_payment_status='completed',
                transaction_legal_approval_status='approved',
                transaction_county__iexact=user.user_county
            ).exclude(transaction_type='verification')
            

            transactions = county_transactions
            
        
    elif user.user_role == 'land_officer':
        user_role_display = "Land Officer"
        commission_type = "Land Commission"

        transactions = Transaction.objects.filter(
            transaction_payment_status='completed',
            transaction_county__iexact=user.user_county
        ).exclude(transaction_type='verification')
        

        
    else:  # admin
        user_role_display = "Administrator"
        commission_type = "Total Commission"
        transactions = Transaction.objects.filter(
            transaction_payment_status='completed'
        )
        if county_filter and county_filter != 'all':
            transactions = transactions.filter(transaction_county__iexact=county_filter)
        

    now = timezone.now()
    if period == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        transactions = transactions.filter(transaction_approved_at__gte=start_date)
    elif period == 'last_month':
        first_day_this_month = now.replace(day=1)
        start_date = (first_day_this_month - timedelta(days=1)).replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        transactions = transactions.filter(transaction_approved_at__range=[start_date, end_date])


    if user.user_role in ['legal_officer', 'land_officer'] and user.user_county:
        county_to_filter = request.GET.get('county', user.user_county)
        if county_to_filter and county_to_filter != 'all':
            transactions = transactions.filter(transaction_county__iexact=county_to_filter)
        elif user.user_county:
            transactions = transactions.filter(transaction_county__iexact=user.user_county)
    

    if user.user_role in ['legal_officer', 'land_officer']:
        transactions = transactions.exclude(transaction_type='verification')
    

    transactions = transactions.select_related(
        'transaction_land_record_id',
        'transaction_from_owner_id',
        'transaction_to_owner_id'
    ).order_by('-transaction_approved_at')
    

    buffer = BytesIO()
    response = HttpResponse(content_type='application/pdf')
    

    if user.user_role == 'admin' and county_filter and county_filter != 'all':
        filename = f"commissions-report-{county_filter}-{datetime.now().strftime('%Y%m%d')}.pdf"
    elif user.user_role in ['legal_officer', 'land_officer']:
        county = request.GET.get('county', user.user_county)
        if county and county != 'all':
            filename = f"commissions-report-{county}-{datetime.now().strftime('%Y%m%d')}.pdf"
        else:
            filename = f"commissions-report-{user.user_county or 'all'}-{datetime.now().strftime('%Y%m%d')}.pdf"
    else:
        filename = f"commissions-report-{datetime.now().strftime('%Y%m%d')}.pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'


    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []
    

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e7e34"),
        spaceAfter=20,
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=12,
        alignment=1,
    )

    elements.append(Paragraph("TITLEGUARD COMMISSIONS REPORT", title_style))
    

    report_details = f"Officer: {user.user_full_name} | Role: {user_role_display}"
    

    display_county = None
    if user.user_role == 'admin':
        if county_filter and county_filter != 'all':
            display_county = county_filter
    else:
        display_county = request.GET.get('county', user.user_county)
        if display_county == 'all':
            display_county = None
    
    if display_county:
        report_details += f" | County: {display_county}"
    
    elements.append(Paragraph(report_details, styles["Normal"]))
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')} | Period: {period.replace('_', ' ').title()}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))


    if transactions.exists():
        

        if user.user_role == 'admin':
            verification_transactions = transactions.filter(transaction_type='verification')
            transfer_transactions = transactions.exclude(transaction_type='verification')
        else:
            transfer_transactions = transactions
            verification_transactions = Transaction.objects.none()

        if user.user_role == 'legal_officer':
            total_commission = 0
            commission_transactions_list = []
            for t in transfer_transactions:
                commission = t.transaction_legal_officer_share if t.transaction_legal_officer_share is not None else 0
                if commission > 0 or (t.transaction_county and t.transaction_county.lower() == user.user_county.lower()):
                    total_commission += float(commission)
                    commission_transactions_list.append(t)
            
            display_transactions = commission_transactions_list
            commission_label = "Total Legal Commission"
            
        elif user.user_role == 'land_officer':
            total_commission = 0
            commission_transactions_list = []
            for t in transfer_transactions:
                commission = t.transaction_land_officer_share if t.transaction_land_officer_share is not None else 0
                if commission > 0 or (t.transaction_county and t.transaction_county.lower() == user.user_county.lower()):
                    total_commission += float(commission)
                    commission_transactions_list.append(t)
            
            display_transactions = commission_transactions_list
            commission_label = "Total Land Commission"
            
        else:  
            total_legal_commission = sum(
                float(t.transaction_legal_officer_share) if t.transaction_legal_officer_share is not None else 0 
                for t in transfer_transactions
            )
            total_land_commission = sum(
                float(t.transaction_land_officer_share) if t.transaction_land_officer_share is not None else 0 
                for t in transfer_transactions
            )
            total_commission = total_legal_commission + total_land_commission
            total_verification_revenue = sum(
                float(t.transaction_amount) if t.transaction_amount is not None else 0 
                for t in verification_transactions
            )
            commission_label = "Total Commission"
            display_transactions = transfer_transactions
        
        total_transactions = len(display_transactions) if user.user_role in ['legal_officer', 'land_officer'] else transactions.count()

        elements.append(Paragraph("Summary", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))

        if user.user_role == 'admin':
            summary_data = [
                ["Metric", "Value"],
                ["Total Transactions", str(total_transactions)],
                ["Verification Transactions", str(verification_transactions.count())],
                ["Transfer Transactions", str(transfer_transactions.count())],
                ["Verification Revenue", f"KES {total_verification_revenue:,.2f}"],
                ["Legal Officer Commission", f"KES {total_legal_commission:,.2f}"],
                ["Land Officer Commission", f"KES {total_land_commission:,.2f}"],
                ["Total Commission", f"KES {total_commission:,.2f}"],
                ["Total Revenue", f"KES {total_verification_revenue + total_commission:,.2f}"],
            ]
        else:
            summary_data = [
                ["Metric", "Value"],
                ["Total Transfer Transactions", str(total_transactions)],
                [commission_label, f"KES {total_commission:,.2f}"],
            ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ])

        if user.user_role == 'admin':
            table_style.add("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.HexColor("#ffffff"),      
                colors.HexColor("#e8f5e8"),      
                colors.HexColor("#d4edda"),     
                colors.HexColor("#d4edda"),      
                colors.HexColor("#d4edda"),      
                colors.HexColor("#d4edda"),      
                colors.HexColor("#e8f5e8"),      
                colors.HexColor("#1e7e34")       
            ])

        summary_table.setStyle(table_style)
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))

        if user.user_role == 'admin':
            data = [["Date", "Type", "Parcel", "Amount", "Legal Commission", "Land Commission", "County"]]
            
            for t in verification_transactions:
                data.append([
                    t.transaction_approved_at.strftime("%Y-%m-%d") if t.transaction_approved_at else t.transaction_created_at.strftime("%Y-%m-%d"),
                    "VERIFICATION",
                    t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                    f"KES {float(t.transaction_amount):,.2f}" if t.transaction_amount else "N/A",
                    "N/A",
                    "N/A",
                    t.transaction_county or "N/A",
                ])
            
            for t in display_transactions:
                data.append([
                    t.transaction_approved_at.strftime("%Y-%m-%d") if t.transaction_approved_at else t.transaction_created_at.strftime("%Y-%m-%d"),
                    "TRANSFER",
                    t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                    f"KES {float(t.transaction_amount):,.2f}" if t.transaction_amount else "N/A",
                    f"KES {float(t.transaction_legal_officer_share):,.2f}" if t.transaction_legal_officer_share is not None else "N/A",
                    f"KES {float(t.transaction_land_officer_share):,.2f}" if t.transaction_land_officer_share is not None else "N/A",
                    t.transaction_county or "N/A",
                ])
            col_widths = [1.2*inch, 1.0*inch, 1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.4*inch]
        elif user.user_role == 'legal_officer':
            data = [["Date", "Parcel", "Transaction Amount", "Your Commission", "County"]]
            for t in display_transactions:
                data.append([
                    t.transaction_approved_at.strftime("%Y-%m-%d") if t.transaction_approved_at else t.transaction_created_at.strftime("%Y-%m-%d"),
                    t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                    f"KES {float(t.transaction_amount):,.2f}" if t.transaction_amount else "N/A",
                    f"KES {float(t.transaction_legal_officer_share):,.2f}" if t.transaction_legal_officer_share is not None else "KES 0.00",
                    t.transaction_county or "N/A",
                ])
            col_widths = [1.3*inch, 1.9*inch, 1.9*inch, 1.9*inch, 1.4*inch]
        else: 
            data = [["Date", "Parcel", "Transaction Amount", "Your Commission", "County"]]
            for t in display_transactions:
                data.append([
                    t.transaction_approved_at.strftime("%Y-%m-%d") if t.transaction_approved_at else t.transaction_created_at.strftime("%Y-%m-%d"),
                    t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                    f"KES {float(t.transaction_amount):,.2f}" if t.transaction_amount else "N/A",
                    f"KES {float(t.transaction_land_officer_share):,.2f}" if t.transaction_land_officer_share is not None else "KES 0.00",
                    t.transaction_county or "N/A",
                ])
            col_widths = [1.3*inch, 1.9*inch, 1.9*inch, 1.9*inch, 1.4*inch]


        if len(data) > 1:  
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No commission transactions found with the current filters.", styles["Normal"]))
    else:
        elements.append(Paragraph("No commission records found for the selected criteria.", styles["Normal"]))


    elements.append(Spacer(1, 0.4 * inch))
    footer_text = f"""
    <para align=center>
    <b>TitleGuard Land Management System</b><br/>
    Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    </para>
    """
    elements.append(Paragraph(footer_text, styles["Normal"]))


    doc.build(elements)
    buffer.seek(0)
    response.write(buffer.read())
    return response

# ===================== TRANSACTIONS REPORT =====================#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_transactions_report(request):
    """Generate Transactions Report with COMPACT SUMMARY"""
    user = request.user
    county = request.GET.get('county')


    if user.user_role in ['admin', 'superadmin']:
        transactions = Transaction.objects.all()
        if county and county != 'all':
            transactions = transactions.filter(transaction_county__iexact=county)
    elif user.user_role in ['land_officer', 'legal_officer']:
        if user.user_county:
            transactions = Transaction.objects.filter(transaction_county__iexact=user.user_county)
        else:
            transactions = Transaction.objects.none()
    else:
        transactions = Transaction.objects.filter(
            Q(transaction_from_owner_id=user) |
            Q(transaction_to_owner_id=user)
        )


    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        transactions = transactions.filter(transaction_legal_approval_status=status_filter)

    search_term = request.GET.get('search')
    if search_term:
        transactions = transactions.filter(
            Q(transaction_land_record_id__land_records_parcel_number__icontains=search_term) |
            Q(transaction_from_owner_id__user_full_name__icontains=search_term) |
            Q(transaction_to_owner_id__user_full_name__icontains=search_term) |
            Q(transaction_payment_reference__icontains=search_term)
        )

    buffer = BytesIO()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions-report-{datetime.now().strftime("%Y-%m-%d")}.pdf"'

    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e7e34"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2c3e50"),
        alignment=1
    )
    normal_style = styles["Normal"]
    normal_style.fontSize = 10

    elements.append(Paragraph("TITLEGUARD LAND MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("TRANSACTIONS REPORT", subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Generated by: {user.user_full_name} ({user.user_role.replace('_', ' ').title()})", normal_style))
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    
    if user.user_role in ['land_officer', 'legal_officer']:
        elements.append(Paragraph(f"County: {user.user_county}", normal_style))
    elif county and county != 'all':
        elements.append(Paragraph(f"County Filter: {county}", normal_style))
    
    if status_filter and status_filter != 'all':
        elements.append(Paragraph(f"Status Filter: {status_filter}", normal_style))
    
    if search_term:
        elements.append(Paragraph(f"Search Filter: {search_term}", normal_style))
    
    elements.append(Spacer(1, 0.2 * inch))

    if not transactions.exists():
        elements.append(Paragraph("No transactions found for your access level.", normal_style))
        doc.build(elements)
        buffer.seek(0)
        response.write(buffer.read())
        return response

    verification_transactions = transactions.filter(transaction_type='verification')
    transfer_transactions = transactions.exclude(transaction_type='verification')


    elements.append(Paragraph("Summary", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    summary_data = [
        ["Total Transactions", str(transactions.count())],
    ]
    
    if user.user_role in ['admin', 'superadmin', 'user']:
        summary_data.extend([
            ["Verification Transactions", str(verification_transactions.count())],
            ["Transfer Transactions", str(transfer_transactions.count())],
        ])
    else:
        summary_data.append(["Transfer Transactions", str(transfer_transactions.count())])
    
    if user.user_role in ['admin', 'superadmin']:
        verification_total = sum(float(t.transaction_amount) for t in verification_transactions if t.transaction_amount)
        transfer_total = sum(float(t.transaction_amount) for t in transfer_transactions if t.transaction_amount)
        
        summary_data.extend([
            ["Verification Revenue", f"KES {verification_total:,.2f}"],
            ["Transfer Revenue", f"KES {transfer_total:,.2f}"],
            ["Total Revenue", f"KES {verification_total + transfer_total:,.2f}"],
        ])

    summary_table = Table(summary_data, colWidths=[2.2*inch, 1.8*inch]) 
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),  
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),   
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),   
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), 
    ]))
    
    if user.user_role in ['admin', 'superadmin']:
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#1e7e34")),  
            ("TEXTCOLOR", (0, 5), (-1, 5), colors.white),
        ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))


    if verification_transactions.exists() and user.user_role in ['admin', 'superadmin', 'user']:
        elements.append(Paragraph("Document Verification Transactions", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        verification_data = [["Document", "Paid By", "Amount", "Payment Status", "Date"]]
        
        for t in verification_transactions:
            verification_data.append([
                t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                t.transaction_from_owner_id.user_full_name if t.transaction_from_owner_id else "N/A",
                f"KES {t.transaction_amount:,.2f}" if t.transaction_amount else "N/A",
                t.transaction_payment_status.upper(),
                t.transaction_created_at.strftime("%Y-%m-%d"),
            ])

        verification_table = Table(verification_data, colWidths=[1.3*inch, 1.8*inch, 2.0*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        verification_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ]))
        elements.append(verification_table)
        elements.append(Spacer(1, 0.3 * inch))

    if transfer_transactions.exists():
        elements.append(Paragraph("Property Transfer Transactions", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        transfer_data = [["Parcel", "From Owner", "To Owner", "Amount", "Approval", "County", "Date"]]
        
        for t in transfer_transactions:
            transfer_data.append([
                t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else "N/A",
                t.transaction_from_owner_id.user_full_name if t.transaction_from_owner_id else "N/A",
                t.transaction_to_owner_id.user_full_name if t.transaction_to_owner_id else "N/A",
                f"KES {t.transaction_amount:,.2f}" if t.transaction_amount else "N/A",
                t.transaction_legal_approval_status.upper(),
                t.transaction_county or "N/A",
                t.transaction_created_at.strftime("%Y-%m-%d"),
            ])

        transfer_table = Table(transfer_data, colWidths=[1.1*inch, 1.3*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.1*inch, 1.1*inch, 1.2*inch])
        transfer_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ]))
        elements.append(transfer_table)

    elements.append(Spacer(1, 0.3 * inch))


    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        normal_style
    ))

    doc.build(elements)
    buffer.seek(0)
    response.write(buffer.read())
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_document_payment(request):
    """
    Initiate M-Pesa payment for document verification (100 KSH)
    """
    document_id = request.data.get('document_id')
    phone_number = request.data.get('phone_number')
    
    try:
        document = Document.objects.get(id=document_id)
        
        if document.document_uploaded_by != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
    
        mpesa_result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=1, 
            account_reference=f"DOC{document.id}",
            transaction_desc="Document Verification Fee"
        )
        
        if mpesa_result['ResponseCode'] == '0':
            payment = Payment.objects.create(
                user=request.user,
                document=document,
                amount=1,
                phone_number=phone_number,
                checkout_request_id=mpesa_result['CheckoutRequestID'],
                merchant_request_id=mpesa_result['MerchantRequestID'],
                status='pending'
            )
            
            return Response({
                'success': True,
                'checkout_request_id': mpesa_result['CheckoutRequestID'],
                'message': 'Payment initiated. Check your phone for STK prompt.'
            })
        else:
            return Response({
                'success': False,
                'error': mpesa_result['ResponseDescription']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request, checkout_id):
    from .models import Transaction
    from django.db.models import Q


    try:
        transaction = Transaction.objects.filter(
            Q(transaction_payment_reference__icontains=checkout_id)
        ).first()

        if not transaction:
            print("❌ Transaction not found in DB")
            return Response({'status': 'not_found'}, status=404)

        print(f"✅ Found transaction: {transaction.transaction_payment_status}")

        return Response({
            'status': transaction.transaction_payment_status,
            'amount': transaction.transaction_amount,
            'reference': transaction.transaction_payment_reference,
        }, status=200)

    except Exception as e:
        print(f"⚠️ Error checking transaction status: {e}")
        return Response({'status': 'error', 'error': str(e)}, status=500)

    

# =========================
# LEGAL CASE VIEWS
# =========================
@api_view(['POST'])
@permission_classes([IsLegalOfficer])
def submit_legal_case(request):
    """
    Legal officer submits a case for land officer review
    """
    expected_fields = ['land_record_id', 'case_type', 'case_title', 'case_description', 'case_priority']
    for field in expected_fields:
        if field in request.data:
            print(f"✅ Field '{field}': {request.data[field]}")
        else:
            print(f"❌ Field '{field}': MISSING")
    
    serializer = LegalCaseCreateSerializer(data=request.data, context={'request': request})
    
    print(f"🔍 Serializer initial data: {serializer.initial_data}")
    
    if serializer.is_valid():
        print(f"✅ Serializer validation PASSED")
        print(f"✅ Validated data: {serializer.validated_data}")
        
        try:
            case = serializer.save()
            
            land_record = case.case_land_record
            legal_officer_county = request.user.user_county
            
            land_record.land_records_verification_status = 'flagged'
            land_record.save()

            land_officers = UserProfile.objects.filter(
                user_role='land_officer',
                user_county=legal_officer_county,
                user_is_active=True
            )
            
            
            for officer in land_officers:
                Notification.objects.create(
                    notification_user_id=officer,
                    notification_title='New Legal Case Submitted',
                    notification_message=(
                        f'Legal case "{case.case_title}" submitted for parcel '
                        f'{land_record.land_records_parcel_number} in {legal_officer_county.replace("_", " ").title()} County. '
                        f'Priority: {case.case_priority}'
                    ),
                    notification_type='warning',
                    notification_related_entity_type='legal_case',
                    notification_related_entity_id=case.case_id
                )

            if land_record.land_records_owner_id:
                Notification.objects.create(
                    notification_user_id=land_record.land_records_owner_id,
                    notification_title='Legal Case Opened on Your Property',
                    notification_message=(
                        f'A legal case has been opened regarding your property {land_record.land_records_parcel_number}. '
                        f'Case: "{case.case_title}". Your property has been temporarily flagged and transfers are suspended until resolution.'
                    ),
                    notification_type='warning',
                    notification_related_entity_type='legal_case',
                    notification_related_entity_id=case.case_id
                )
                print(f"Notified land owner: {land_record.land_records_owner_id.user_full_name}")
            else:
                print("⚠️ No land owner found to notify")


            if case.case_priority in ['high', 'urgent']:
                admins = UserProfile.objects.filter(user_role__in=['admin', 'superadmin'])
                for admin in admins:
                    Notification.objects.create(
                        notification_user_id=admin,
                        notification_title='High Priority Legal Case',
                        notification_message=(
                            f'High priority legal case "{case.case_title}" submitted for '
                            f'{land_record.land_records_parcel_number} in {legal_officer_county.replace("_", " ").title()} County.'
                        ),
                        notification_type='warning'
                    )

            Notification.objects.create(
                notification_user_id=request.user,
                notification_title='Case Submitted Successfully',
                notification_message=(
                    f'Your legal case "{case.case_title}" has been submitted and assigned to '
                    f'{land_officers.count()} land officer(s) in {legal_officer_county.replace("_", " ").title()} County.'
                ),
                notification_type='success'
            )

            response_serializer = LegalCaseSubmissionSerializer(case)
            return Response({
                'message': f'Legal case submitted successfully. Notified {land_officers.count()} land officer(s) in {legal_officer_county.replace("_", " ").title()} County.',
                'case': response_serializer.data,
                'notified_officers_count': land_officers.count(),
                'county': legal_officer_county
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f" Error during case creation: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to submit legal case: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        for field, errors in serializer.errors.items():
            print(f"   - {field}: {errors}")
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_legal_cases(request):
    """
    Get legal cases - filtered by user role and county
    """
    user = request.user
    
    if user.user_role == 'admin':
        cases = LegalCaseSubmission.objects.all().order_by('-case_created_at')
        
    elif user.user_role == 'legal_officer':
        cases = LegalCaseSubmission.objects.filter(case_legal_officer=user)
    
    elif user.user_role == 'land_officer':
        if user.user_county:
            cases = LegalCaseSubmission.objects.filter(
                case_land_record__land_records_county__iexact=user.user_county
            )
        else:
            cases = LegalCaseSubmission.objects.none()
    
    else:
        cases = LegalCaseSubmission.objects.filter(
            case_land_record__land_records_owner_id=user
        )
    
    serializer = LegalCaseSubmissionSerializer(cases, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsLandOfficer | IsLegalOfficer])
def update_case_status(request, case_id):
    """
    Land officer updates case status and adds notes
    """
    try:
        case = LegalCaseSubmission.objects.get(case_id=case_id)
    except LegalCaseSubmission.DoesNotExist:
        return Response({'error': 'Case not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    notes = request.data.get('land_officer_notes', '')
    
    if new_status not in ['under_review', 'resolved', 'dismissed']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    old_status = case.case_status
    case.case_status = new_status
    case.case_land_officer_notes = notes
    case.save()


    Notification.objects.create(
        notification_user_id=case.case_legal_officer,
        notification_title=f'Case Status Updated',
        notification_message=f'Case "{case.case_title}" status changed from {old_status.replace("_", " ").title()} to {new_status.replace("_", " ").title()}.',
        notification_type='info'
    )


    land_record = case.case_land_record
    if land_record.land_records_owner_id:
        Notification.objects.create(
            notification_user_id=land_record.land_records_owner_id,
            notification_title=f'Case Status Update',
            notification_message=f'Legal case regarding your property {land_record.land_records_parcel_number} has been updated to: {new_status.replace("_", " ").title()}.',
            notification_type='info'
        )

    # ========== SPECIAL HANDLING FOR RESOLVED/DISMISSED CASES ==========
    if new_status in ['resolved', 'dismissed']:
        land_record.land_records_verification_status = 'verified'
        land_record.save()

        Notification.objects.create(
            notification_user_id=case.case_legal_officer,
            notification_title=f'Case {new_status.title()} Successfully',
            notification_message=f'Case "{case.case_title}" has been {new_status}. Land record {land_record.land_records_parcel_number} has been unflagged.',
            notification_type='success'
        )


        if land_record.land_records_owner_id:
            Notification.objects.create(
                notification_user_id=land_record.land_records_owner_id,
                notification_title='Property Restrictions Lifted',
                notification_message=(
                    f'Your land record {land_record.land_records_parcel_number} has been unflagged and is now transferable. '
                    f'The legal case "{case.case_title}" has been {new_status}.'
                ),
                notification_type='success'
            )


        land_officers = UserProfile.objects.filter(
            user_role='land_officer',
            user_county=land_record.land_records_county,
            user_is_active=True
        )
        
        for officer in land_officers:
            Notification.objects.create(
                notification_user_id=officer,
                notification_title=f'Case {new_status.title()} in {land_record.land_records_county}',
                notification_message=f'Legal case "{case.case_title}" for parcel {land_record.land_records_parcel_number} has been {new_status}.',
                notification_type='success'
            )

        if case.case_priority in ['high', 'urgent']:
            admins = UserProfile.objects.filter(user_role__in=['admin', 'superadmin'])
            for admin in admins:
                Notification.objects.create(
                    notification_user_id=admin,
                    notification_title=f'High Priority Case {new_status.title()}',
                    notification_message=f'High priority case "{case.case_title}" for {land_record.land_records_parcel_number} has been {new_status}.',
                    notification_type='info'
                )

    # ========== SPECIAL HANDLING FOR UNDER REVIEW ==========
    elif new_status == 'under_review':
        Notification.objects.create(
            notification_user_id=case.case_legal_officer,
            notification_title='Case Under Active Review',
            notification_message=f'Case "{case.case_title}" is now under active review by land officers.',
            notification_type='info'
        )

    serializer = LegalCaseSubmissionSerializer(case)
    return Response({
        'message': f'Case status updated to {new_status}',
        'case': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_legal_cases_report(request):
    """
    Download Legal Cases Report as PDF - Filtered by user role and county
    """
    user = request.user
    
    if user.user_role == 'admin':
        cases = LegalCaseSubmission.objects.all().order_by('-case_created_at')
    elif user.user_role == 'legal_officer':
        cases = LegalCaseSubmission.objects.filter(case_legal_officer=user)
    elif user.user_role == 'land_officer':
        if user.user_county:
            cases = LegalCaseSubmission.objects.filter(
                case_land_record__land_records_county__iexact=user.user_county
            )
        else:
            cases = LegalCaseSubmission.objects.none()
    else:
        cases = LegalCaseSubmission.objects.filter(
            case_land_record__land_records_owner_id=user
        )
    
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        cases = cases.filter(case_status=status_filter)
    
    search_term = request.GET.get('search')
    if search_term:
        cases = cases.filter(
            Q(case_title__icontains=search_term) |
            Q(case_land_record__land_records_parcel_number__icontains=search_term) |
            Q(case_type__icontains=search_term)
        )
    
    buffer = BytesIO()
    response = HttpResponse(content_type='application/pdf')
    
    filename = f"legal-cases-report-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle(
        "TitleGuardTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e7e34"),
        spaceAfter=20,
        alignment=1,
    )
    
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=12,
        alignment=1,
    )
    
    normal_style = styles["Normal"]
    normal_style.fontSize = 10
    normal_style.leading = 13
    
 
    elements.append(Paragraph("TITLEGUARD LAND MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("LEGAL CASES REPORT", subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))
    
 
    elements.append(Paragraph(f"Generated by: {user.user_full_name} ({user.user_role.replace('_', ' ').title()})", normal_style))
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    
    if user.user_role in ['land_officer', 'legal_officer'] and user.user_county:
        elements.append(Paragraph(f"County: {user.user_county.replace('_', ' ').title()}", normal_style))
    
    if status_filter and status_filter != 'all':
        elements.append(Paragraph(f"Status Filter: {status_filter.replace('_', ' ').title()}", normal_style))
    
    if search_term:
        elements.append(Paragraph(f"Search Filter: {search_term}", normal_style))
    
    elements.append(Spacer(1, 0.2 * inch))
    
    if not cases.exists():
        elements.append(Paragraph("No legal cases found matching the specified criteria.", normal_style))
        doc.build(elements)
        buffer.seek(0)
        response.write(buffer.read())
        return response
    
  
    total_cases = cases.count()
    status_counts = cases.annotate(
        normalized_status=Lower('case_status')
    ).values('normalized_status').annotate(
        count=Count('case_id')
    ).order_by('normalized_status')

    stats_data = [["Status", "Count"]]
    for stat in status_counts:
        status_display = stat['normalized_status'].replace('_', ' ').title()
        stats_data.append([status_display, str(stat['count'])])

    stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
    ]))

    elements.append(Paragraph("Case Statistics", subtitle_style))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3 * inch))
    

    elements.append(Paragraph("Case Details", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    data = [[
        "Case Title", 
        "Parcel Number", 
        "Case Type", 
        "Status", 
        "Priority", 
        "Legal Officer",
        "Created Date"
    ]]
    
    for case in cases:
        parcel_number = "N/A"
        if case.case_land_record:
            parcel_number = case.case_land_record.land_records_parcel_number
        
        legal_officer_name = "Not Assigned"
        if case.case_legal_officer:
            legal_officer_name = case.case_legal_officer.user_full_name
        
        data.append([
            case.case_title[:30] + "..." if len(case.case_title) > 30 else case.case_title,
            parcel_number,
            case.case_type.replace('_', ' ').title(),
            case.case_status.replace('_', ' ').title(),
            case.case_priority.title(),
            legal_officer_name[:20] + "..." if len(legal_officer_name) > 20 else legal_officer_name,
            case.case_created_at.strftime("%Y-%m-%d")
        ])
    
    table = Table(data, colWidths=[2.0*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.0*inch, 1.8*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e7e34")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))
    
    elements.append(Paragraph("Case Descriptions", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    for i, case in enumerate(cases[:10]):
        elements.append(Paragraph(f"<b>Case {i+1}: {case.case_title}</b>", normal_style))
        

        details_text = f"""
        <b>Parcel:</b> {case.case_land_record.land_records_parcel_number if case.case_land_record else 'N/A'} | 
        <b>Type:</b> {case.case_type.replace('_', ' ').title()} | 
        <b>Status:</b> {case.case_status.replace('_', ' ').title()} | 
        <b>Priority:</b> {case.case_priority.title()}
        """
        elements.append(Paragraph(details_text, normal_style))
        
 
        description = case.case_description
        if len(description) > 200:
            description = description[:200] + "..."
        elements.append(Paragraph(f"<b>Description:</b> {description}", normal_style))
        

        if case.case_land_officer_notes:
            notes = case.case_land_officer_notes
            if len(notes) > 150:
                notes = notes[:150] + "..."
            elements.append(Paragraph(f"<b>Officer Notes:</b> {notes}", normal_style))
        
        elements.append(Spacer(1, 0.1 * inch))
    
    if cases.count() > 10:
        elements.append(Paragraph(f"... and {cases.count() - 10} more cases", normal_style))
    
    elements.append(Spacer(1, 0.3 * inch))
    

    footer_text = f"""
    <para align=center>
    <b>TitleGuard Land Management System</b><br/>
    Legal Cases Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    Total Cases: {total_cases} 
    </para>
    """
    elements.append(Paragraph(footer_text, normal_style))
    
    
    doc.build(elements)
    buffer.seek(0)
    response.write(buffer.read())
    
    return response
    




# --------------------------------------------------------------------------
# 1. Verification Payment Initiation
# --------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_verification_payment(request):
    """
    Initiate M-Pesa payment for document verification (KES 100)
    """
    document_id = request.data.get('document_id')
    phone_number = request.data.get('phone_number')
    
    if not document_id or not phone_number:
        return Response({'error': 'Document ID and phone number are required'}, status=400)

    try:
        document = Document.objects.get(document_id=document_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=404)

    if document.document_uploaded_by != request.user:
        return Response({'error': 'Not authorized to pay for this document'}, status=403)

    if document.document_status != 'pending_payment':
        return Response({'error': 'Document is not awaiting payment'}, status=400)

    formatted_phone = phone_number.replace(' ', '')
    if formatted_phone.startswith('0'):
        formatted_phone = '254' + formatted_phone[1:]


    if formatted_phone.startswith(("254712", "254799", "254700", "254740")):
        fake_checkout = f"DOC_SIMULATED_{random.randint(1000,9999)}"
        
 
        document.document_status = 'payment_completed'
        document.save()
        
        from decimal import Decimal 
        

        transaction = Transaction.objects.create(
            transaction_type='verification',
            transaction_amount=Decimal('100.00'),
            transaction_payment_reference=fake_checkout,
            transaction_payment_status='completed',
            transaction_from_owner_id=request.user,
            transaction_to_owner_id=request.user, 
            transaction_land_record_id=document.document_land_records_id,
            transaction_legal_approval_status='approved',
            transaction_transfer_completed=True
        )
        
        # Trigger OCR processing
        from .utils import process_ocr
        try:
            process_ocr(document)
        except Exception as e:
            print(f"OCR processing error: {str(e)}")
        
        return Response({
            'success': True,
            'checkout_request_id': fake_checkout,
            'message': 'Payment successful and OCR verification started.',
        }, status=200)

    # REAL M-PESA
    try:
        from decimal import Decimal 
        mpesa_result = initiate_mpesa_payment(
            phone_number=formatted_phone,
            amount=1,
            description=f"Document Verification - {document.document_file_name[:30]}",
            user_profile=request.user
        )
        
        if mpesa_result.get('success'):
            document.document_status = 'pending_mpesa' 
            document.save()
            
            # Create transaction with PENDING status
            Transaction.objects.create(
                transaction_type='verification',
                transaction_amount=Decimal('100.00'),
                transaction_payment_reference=mpesa_result['checkout_request_id'],
                transaction_payment_status='pending',
                transaction_from_owner_id=request.user,
                transaction_to_owner_id=request.user,
                transaction_land_record_id=document.document_land_records_id,
                transaction_legal_approval_status='pending',
            )
            
            return Response({
                'success': True,
                'checkout_request_id': mpesa_result['checkout_request_id'],
                'message': 'Payment initiated successfully. Check your phone.',
            }, status=200)
        else:
            return Response({
                'success': False,
                'error': mpesa_result.get('error', 'Payment initiation failed')
            }, status=400)
            
    except Exception as e:
        print(f"Payment initiation error: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


# --------------------------------------------------------------------------
# 2. M-Pesa Callback Handler
# --------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    Handle M-PESA callback for both transfers and verifications
    """
    from decimal import Decimal
    from .models import Transaction, Notification, Document
    from .serializers import PaymentCallbackSerializer


    body = request.data.get('Body', {}).get('stkCallback', {})
    result_code = body.get('ResultCode')
    result_desc = body.get('ResultDesc')
    checkout_id = body.get('CheckoutRequestID')

    print(f"🔔 M-Pesa Callback received: {checkout_id}, Result: {result_code}")

    try:
        transaction = Transaction.objects.get(transaction_payment_reference=checkout_id)
    except Transaction.DoesNotExist:
        print(f"⚠️ Transaction not found for CheckoutRequestID: {checkout_id}")
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    if result_code == 0: 
        callback_data = body.get('CallbackMetadata', {}).get('Item', [])
        receipt = next((i['Value'] for i in callback_data if i['Name'] == 'MpesaReceiptNumber'), None)
        amount = next((Decimal(i['Value']) for i in callback_data if i['Name'] == 'Amount'), transaction.transaction_amount) # Use Decimal here

        transaction.transaction_payment_status = 'completed'
        transaction.mpesa_receipt_number = receipt
        transaction.transaction_payment_reference = receipt or transaction.transaction_payment_reference
        transaction.transaction_amount = amount
        transaction.save()
        
  
        if transaction.transaction_type == 'verification':
            try:
                document = Document.objects.filter(
                    document_uploaded_by=transaction.transaction_from_owner_id,
                    document_status__in=['pending_mpesa', 'pending_payment']
                ).latest('document_created_at')
                document.document_status = 'payment_completed'
                document.save()
                
                # Trigger OCR processing
                from .utils import process_ocr
                process_ocr(document)
                
            except Document.DoesNotExist:
                print(" No document found for verification payment after success")
        
       
        elif transaction.transaction_type in ['transfer', 'sale']:
            transaction.assign_officers_by_county()
            transaction.transaction_legal_approval_status = 'approved'
            transaction.transaction_approved_at = timezone.now()
            transaction.transaction_legal_officer_share = Decimal('350.00')
            transaction.transaction_land_officer_share = Decimal('650.00')
            transaction.save()


      
        Notification.objects.create(
            notification_user_id=transaction.transaction_from_owner_id,
            notification_title='Payment Successful',
            notification_message=f'KES {amount} paid successfully for {transaction.transaction_type}.',
            notification_type='success'
        )

        print(f"✅ Payment completed for {checkout_id}")
        return Response({'message': 'Payment completed successfully'}, status=status.HTTP_200_OK)

    else:  
        transaction.transaction_payment_status = 'failed'
        transaction.save()

        Notification.objects.create(
            notification_user_id=transaction.transaction_from_owner_id,
            notification_title='Payment Failed',
            notification_message=f'M-PESA payment failed: {result_desc}',
            notification_type='error'
        )

        print(f" Payment failed for {checkout_id}: {result_desc}")
        return Response({'message': 'Payment failed'}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ownership_history(request, land_record_id):
    """
    Get ownership history for a land record
    """
    try:
        land_record = LandRecord.objects.get(land_records_id=land_record_id)
    except LandRecord.DoesNotExist:
        return Response(
            {'error': 'Land record not found'},
            status=status.HTTP_404_NOT_FOUND
        )

  
    user = request.user
    if user.user_role == 'user' and land_record.land_records_owner_id != user and land_record.land_records_previous_owner != user:
        return Response(
            {'error': 'You can only view history of your own land records'},
            status=status.HTTP_403_FORBIDDEN
        )

    history = OwnershipHistory.objects.filter(history_land_record=land_record).order_by('-history_transfer_date')
    serializer = OwnershipHistorySerializer(history, many=True)
    
    return Response({
        'land_record': {
            'parcel_number': land_record.land_records_parcel_number,
            'current_deed_number': land_record.land_records_deed_number,
            'current_owner': land_record.land_records_owner_id.user_full_name if land_record.land_records_owner_id else 'N/A'
        },
        'history': serializer.data
    })
    


def initiate_transfer_after_payment(transaction):
    land_record = transaction.transaction_land_record_id
    buyer = transaction.transaction_to_owner_id
    seller = transaction.transaction_from_owner_id

    Notification.objects.create(
        notification_user=seller,
        notification_title="Transfer Payment Complete",
        notification_message=f"Payment confirmed for parcel {land_record.land_records_parcel_number}.",
        notification_type="payment"
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_all_transactions(request):
    transactions = Transaction.objects.all().select_related(
        'transaction_land_record_id',
        'transaction_from_owner_id',
        'transaction_to_owner_id'
    ).order_by('-transaction_created_at')
    
    debug_data = []
    for t in transactions:
        debug_data.append({
            'transaction_id': str(t.transaction_id),
            'parcel_number': t.transaction_land_record_id.land_records_parcel_number if t.transaction_land_record_id else 'NO LAND RECORD',
            'from_owner': t.transaction_from_owner_id.user_full_name if t.transaction_from_owner_id else 'NO FROM OWNER',
            'to_owner': t.transaction_to_owner_id.user_full_name if t.transaction_to_owner_id else 'NO TO OWNER',
            'transaction_type': t.transaction_type,
            'amount': float(t.transaction_amount) if t.transaction_amount else 0,
            'payment_status': t.transaction_payment_status,
            'legal_approval_status': t.transaction_legal_approval_status,
            'transfer_accepted': t.transfer_accepted,
            'transfer_rejected': t.transfer_rejected,
            'payment_reference': t.transaction_payment_reference,
            'created_at': t.transaction_created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'has_legal_officer': bool(t.transaction_legal_officer_id),
            'has_land_officer': bool(t.transaction_land_officer_id)
        })
    
    return Response({
        'total_transactions': transactions.count(),
        'transactions': debug_data
    })
    
    
