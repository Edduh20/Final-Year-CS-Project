from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail, EmailMessage  
from django.conf import settings
import uuid
import secrets
from datetime import timedelta
from django.utils import timezone
import os
import socket

def default_acceptance_expiry():
    return timezone.now() + timedelta(days=7)


# =========================
# USER TABLE
# =========================
class UserProfileManager(BaseUserManager):
    def create_user(self, user_email, password=None, **extra_fields):
        if not user_email:
            raise ValueError('Users must have an email address')
        user_email = self.normalize_email(user_email)
        user = self.model(user_email=user_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_email, password=None, **extra_fields):
        extra_fields.setdefault('user_role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_full_name', 'System Administrator')
        extra_fields.setdefault('user_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(user_email=user_email, password=password, **extra_fields)

class UserProfile(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('land_officer', 'Land Officer'),
        ('legal_officer', 'Legal Officer'),
        ('user', 'User'),
    ]
    
        
    COUNTY_CHOICES = [
        ('nairobi', 'Nairobi'),
        ('mombasa', 'Mombasa'),
        ('kwale', 'Kwale'),
        ('kilifi', 'Kilifi'),
        ('tana_river', 'Tana River'),
        ('lamu', 'Lamu'),
        ('taita_taveta', 'Taita Taveta'),
        ('garissa', 'Garissa'),
        ('wajir', 'Wajir'),
        ('mandera', 'Mandera'),
        ('marsabit', 'Marsabit'),
        ('isiolo', 'Isiolo'),
        ('meru', 'Meru'),
        ('tharaka_nithi', 'Tharaka-Nithi'),
        ('embu', 'Embu'),
        ('kitui', 'Kitui'),
        ('machakos', 'Machakos'),
        ('makueni', 'Makueni'),
        ('nyandarua', 'Nyandarua'),
        ('nyeri', 'Nyeri'),
        ('kirinyaga', 'Kirinyaga'),
        ('muranga', 'Murang\'a'),
        ('kiambu', 'Kiambu'),
        ('turkana', 'Turkana'),
        ('west_pokot', 'West Pokot'),
        ('samburu', 'Samburu'),
        ('trans_nzoia', 'Trans Nzoia'),
        ('uasin_gishu', 'Uasin Gishu'),
        ('elgeyo_marakwet', 'Elgeyo-Marakwet'),
        ('nandi', 'Nandi'),
        ('baringo', 'Baringo'),
        ('laikipia', 'Laikipia'),
        ('nakuru', 'Nakuru'),
        ('narok', 'Narok'),
        ('kajiado', 'Kajiado'),
        ('kericho', 'Kericho'),
        ('bomet', 'Bomet'),
        ('kakamega', 'Kakamega'),
        ('vihiga', 'Vihiga'),
        ('bungoma', 'Bungoma'),
        ('busia', 'Busia'),
        ('siaya', 'Siaya'),
        ('kisumu', 'Kisumu'),
        ('homa_bay', 'Homa Bay'),
        ('migori', 'Migori'),
        ('kisii', 'Kisii'),
        ('nyamira', 'Nyamira'),
    ]



    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='User_id')
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', db_column='User_role')
    user_full_name = models.CharField(max_length=255, db_column='User_full_name')
    user_phone_number = models.CharField(max_length=20, null=True, blank=True, db_column='User_phone_number')
    user_id_number = models.CharField(max_length=20, unique=True, null=True, blank=True, db_column='User_id_number')
    user_is_registered = models.BooleanField(default=True, db_column='User_is_registered')
    user_email = models.EmailField(unique=True, db_column='User_email')
    user_is_active = models.BooleanField(default=True, db_column='User_is_active')
    password = models.CharField(max_length=128, db_column='User_password') 
    is_superuser = models.BooleanField(default=False, db_column='User_is_superuser')
    is_staff = models.BooleanField(default=False, db_column='User_is_staff')
    
    last_login = None

    
    user_county = models.CharField(
        max_length=20, 
        choices=COUNTY_CHOICES, 
        null=True, 
        blank=True,
        db_column='User_county'
    )
    
    
    user_email_verified = models.BooleanField(default=False, db_column='User_email_verified')
    user_email_otp = models.CharField(max_length=6, null=True, blank=True, db_column='User_email_otp')
    user_email_otp_created_at = models.DateTimeField(null=True, blank=True, db_column='User_email_otp_created_at')
    user_first_login_completed = models.BooleanField(default=False, db_column='User_first_login_completed')
    user_created_at = models.DateTimeField(auto_now_add=True, db_column='User_created_at')
    user_updated_at = models.DateTimeField(auto_now=True, db_column='User_updated_at')

    objects = UserProfileManager()

    USERNAME_FIELD = 'user_email'
    REQUIRED_FIELDS = ['user_full_name']

    class Meta:
        db_table = 'User'
        ordering = ['-user_created_at']

    def __str__(self):
        return f"{self.user_full_name} ({self.user_role})"
    
    def generate_otp(self, temp_password=None):
        self.user_email_otp = str(secrets.randbelow(1000000)).zfill(6)
        self.user_email_otp_created_at = timezone.now()
        self.save()

        from django.utils.timezone import localtime
        from decouple import config

        frontend_url = config("FRONTEND_URL")

        subject = f'TitleGuard - OTP Verification for {self.user_full_name}'

        password_section = f"\n🔑 TEMPORARY PASSWORD: {temp_password}\n" if temp_password else ""

        message = f"""
        🔐 TITLEGUARD SYSTEM - OTP VERIFICATION
        
        Name: {self.user_full_name}
        Email: {self.user_email}
        Role: {self.get_user_role_display()}
        
        📧 OTP CODE: {self.user_email_otp}
        {password_section}
        
        Verification Link:
        {frontend_url}/verify-otp

        ⚠️ OTP expires in 10 minutes

        Timestamp: {localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")}
        """

        import requests as http_requests
        brevo_api_key = config('BREVO_API_KEY', default='').strip()
        print(f"DEBUG API KEY: {brevo_api_key[:10]}...")
        print(f"DEBUG KEY LENGTH: {len(brevo_api_key)}")
        print(f"DEBUG KEY: {brevo_api_key}")

        if brevo_api_key:
            try:
                response = http_requests.post(
                    'https://api.brevo.com/v3/smtp/email',
                    headers={
                        'api-key': brevo_api_key,
                        'Content-Type': 'application/json'
                    },
                    json={
                        'sender': {'email': settings.DEFAULT_FROM_EMAIL},
                        'to': [{'email': self.user_email}],
                        'subject': subject,
                        'textContent': message
                    },
                    timeout=10
                )
                print(f"📧 Email sent via Brevo API: {response.status_code}")
                print(f"📧 Brevo status: {response.status_code}")
                print(f"📧 Brevo error: {response.text}")
            except Exception as e:
                print(f"Email send failed: {str(e)}")

        
        
        
    def verify_otp(self, otp):
        if not self.user_email_otp or not self.user_email_otp_created_at:
            return False
        
        if timezone.now() > self.user_email_otp_created_at + timedelta(minutes=10):
            return False
        
        if self.user_email_otp == otp:
            self.user_email_verified = True
            self.user_email_otp = None
            self.user_email_otp_created_at = None
            self.save()
            return True
        
        return False

    @property
    def role(self):
        return self.user_role


# =========================
# LAND RECORDS TABLE
# =========================
class LandRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
        ('transferred', 'Transferred'),  
    ]

    land_records_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Land_records_id')
    land_records_parcel_number = models.CharField(max_length=100, unique=True, db_column='Land_records_parcel_number')
    land_records_deed_number = models.CharField(max_length=100, unique=True, db_column='Land_records_deed_number')
    land_records_owner_id = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_land_records',  
        db_column='Land_records_owner_id'
    )
    land_records_previous_owner = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_land_records',
        db_column='Land_records_previous_owner'
    )
    land_records_location = models.CharField(max_length=255, db_column='Land_records_location')
    land_records_county = models.CharField(
        max_length=20, 
        choices=UserProfile.COUNTY_CHOICES,
        db_column='Land_records_county'
    )
    land_records_size = models.DecimalField(max_digits=10, decimal_places=2, db_column='Land_records_size')
    land_records_verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_column='Land_records_verification_status')
    land_records_registered_date = models.DateTimeField(auto_now_add=True, db_column='Land_records_registered_date')
    land_records_transfer_date = models.DateTimeField(null=True, blank=True, db_column='Land_records_transfer_date') 
    land_records_created_at = models.DateTimeField(auto_now_add=True, db_column='Land_records_created_at')
    land_records_updated_at = models.DateTimeField(auto_now=True, db_column='Land_records_updated_at')
    land_records_first_registration_date = models.DateTimeField(auto_now_add=True,db_column='Land_records_first_registration_date'
)



    def generate_new_deed_number(self):
        original_deed = self.land_records_deed_number

        if "-" in original_deed:
            base, version = original_deed.split("-")
            try:
                new_version = int(version) + 1
                return f"{base}-{new_version}"
            except ValueError:
                pass

        if original_deed:
            return f"{original_deed}-2"

        county = (self.land_records_county or "UNKNOWN").upper()
        parcel = self.land_records_parcel_number.replace("/", "").replace("LR", "")
        
        digits = ''.join([c for c in parcel if c.isdigit()]) or "0000"

        return f"TD/{county}/{digits}"


    def transfer_ownership(self, new_owner, transaction=None):
        """Transfer ownership to new owner and track history"""
        old_deed_number = self.land_records_deed_number
        new_deed_number = self.generate_new_deed_number()

        # ownership
        self.land_records_previous_owner = self.land_records_owner_id
        self.land_records_owner_id = new_owner

        # deed + legal dates
        self.land_records_deed_number = new_deed_number
        self.land_records_verification_status = 'transferred'
        self.land_records_transfer_date = timezone.now()
        self.land_records_registered_date = timezone.now() 
        
        self.save()


        OwnershipHistory.objects.create(
            history_land_record=self,
            history_previous_owner=self.land_records_previous_owner,
            history_new_owner=new_owner,
            history_transfer_type=transaction.transaction_type if transaction else 'transfer',
            history_transaction=transaction,
            history_deed_number_old=old_deed_number,
            history_deed_number_new=new_deed_number,
            history_notes=f"Transfer completed on {timezone.now().strftime('%Y-%m-%d')}"
        )
        
        return new_deed_number

    class Meta:
        db_table = 'Land_records'
        ordering = ['-land_records_created_at']

    def __str__(self):
        return f"{self.land_records_parcel_number} - {self.land_records_location}"


def link_existing_land_records(user):
    """
    Automatically link land records to a user if their ID number matches.
    """
    if not user.user_id_number:
        return

 
    matching_records = LandRecord.objects.filter(
        land_records_owner_id__isnull=True,
        land_records_id_number=str(user.user_id_number).strip()
    )

    updated_count = matching_records.update(land_records_owner_id=user)

    if updated_count > 0:
        print(f"✅ Linked {updated_count} land record(s) to {user.user_full_name} ({user.user_id_number})")


# =========================
# DOCUMENT TABLE
# =========================
class Document(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('payment_completed', 'Payment Completed'),
        ('processing', 'Processing - OCR in Progress'),  
        ('verified', 'Verified - OCR Complete'),
        ('rejected', 'Rejected - OCR Failed'),
        ('needs_review', 'Needs Manual Review'), 
    ]

    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Document_id')
    document_land_records_id = models.ForeignKey(
        LandRecord,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        db_column='Document_land_records_id'
    )
    document_uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        db_column='Document_uploaded_by'
    )
    document_file_url = models.CharField(max_length=500, db_column='Document_file_url')
    document_file_name = models.CharField(max_length=255, db_column='Document_file_name')
    document_file_type = models.CharField(max_length=50, null=True, blank=True, db_column='Document_file_type')
    document_ocr_text = models.TextField(null=True, blank=True, db_column='Document_ocr_text')
    document_ocr_metadata = models.JSONField(null=True, blank=True, db_column='Document_ocr_metadata')
    document_verification_notes = models.TextField(null=True, blank=True, db_column='Document_verification_notes')
    document_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment', db_column='Document_status')
    document_created_at = models.DateTimeField(auto_now_add=True, db_column='Document_created_at')

    class Meta:
        db_table = 'Document'
        ordering = ['-document_created_at']

    def __str__(self):
        return f"{self.document_file_name} - {self.document_status}"


# =========================
# TRANSACTION TABLE
# =========================
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('transfer', 'Transfer'),
        ('inheritance', 'Inheritance'),
        ('gift', 'Gift'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Transaction_id')
    transaction_land_record_id = models.ForeignKey(
        LandRecord,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        db_column='Transaction_land_record_id'
    )
    transaction_from_owner_id = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions_from',
        db_column='Transaction_from_owner_id'
    )
    
    transaction_to_owner_id_number = models.CharField(
        max_length=20,
        db_column='Transaction_to_owner_id_number',
        help_text="ID Number of the new owner"
    )
    
    transaction_to_owner_id = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_to',
        db_column='Transaction_to_owner_id'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, db_column='Transaction_type')
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, db_column='Transaction_amount')
    transaction_payment_reference = models.CharField(max_length=100, null=True, blank=True, db_column='Transaction_payment_reference')
    transaction_payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', db_column='Transaction_payment_status')
    transaction_county = models.CharField(
        max_length=20, 
        choices=UserProfile.COUNTY_CHOICES,
        null=True,
        blank=True,
        db_column='Transaction_county'
    )
    transaction_legal_officer_id = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='legal_transactions',
        db_column='Transaction_legal_officer_id'
    )
    
    transaction_legal_approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', db_column='Transaction_legal_approval_status')
    transaction_legal_notes = models.TextField(null=True, blank=True, db_column='Transaction_legal_notes')
    transaction_approved_at = models.DateTimeField(null=True, blank=True, db_column='Transaction_approved_at')
    transaction_created_at = models.DateTimeField(auto_now_add=True, db_column='Transaction_created_at')


    transaction_land_officer_id = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='land_transactions',
        db_column='Transaction_land_officer_id'
    )
    
    transaction_land_officer_share = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, db_column='Transaction_land_officer_share'
    )
    transaction_legal_officer_share = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, db_column='Transaction_legal_officer_share'
    )

    transaction_transfer_completed = models.BooleanField(default=False, db_column='Transaction_transfer_completed')
    transaction_new_deed_number = models.CharField(max_length=100, null=True, blank=True, db_column='Transaction_new_deed_number')

    class Meta:
        db_table = 'Transaction'
        ordering = ['-transaction_created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_land_record_id.land_records_parcel_number if self.transaction_land_record_id else 'N/A'}"

    def resolve_to_owner(self):
        """
        Resolve the ID number to an actual user profile
        """
        if not self.transaction_to_owner_id and self.transaction_to_owner_id_number:
            try:
                user = UserProfile.objects.get(user_id_number=self.transaction_to_owner_id_number)
                self.transaction_to_owner_id = user
                self.save()
                return user
            except UserProfile.DoesNotExist:
                return None
        return self.transaction_to_owner_id
    
    def assign_officers_by_county(self):
        """Automatically assign officers based on land record county"""
        if not self.transaction_land_record_id:
            return
            
        county = self.transaction_land_record_id.land_records_county
        self.transaction_county = county
        
        legal_officers = UserProfile.objects.filter(
            user_role='legal_officer',
            user_county=county,
            user_is_active=True
        )
        
        if legal_officers.exists():
            self.transaction_legal_officer_id = legal_officers.first()
        
        land_officers = UserProfile.objects.filter(
            user_role='land_officer',
            user_county=county,
            user_is_active=True
        )
        
        if land_officers.exists():
            self.transaction_land_officer_id = land_officers.first()
        
        self.save()
# =========================
# NOTIFICATION TABLE
# =========================
class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Notification_id')
    notification_user_id = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        db_column='Notification_user_id'
    )
    notification_title = models.CharField(max_length=255, db_column='Notification_title')
    notification_message = models.TextField(db_column='Notification_message')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info', db_column='Notification_type')
    notification_related_entity_type = models.CharField(max_length=50, null=True, blank=True, db_column='Notification_related_entity_type')
    notification_related_entity_id = models.UUIDField(null=True, blank=True, db_column='Notification_related_entity_id')
    notification_read = models.BooleanField(default=False, db_column='Notification_read')
    notification_created_at = models.DateTimeField(auto_now_add=True, db_column='Notification_created_at')

    class Meta:
        db_table = 'Notification'
        ordering = ['-notification_created_at']

    def __str__(self):
        return f"{self.notification_title} - {self.notification_user_id.user_full_name if self.notification_user_id else 'N/A'}"


    
# =========================
# LEGAL CASE SUBMISSION TABLE
# =========================
class LegalCaseSubmission(models.Model):
    CASE_TYPES = [
        ('dispute', 'Boundary Dispute'),
        ('inheritance', 'Inheritance Dispute'),
        ('fraud', 'Fraud Case'),
        ('multiple_claim', 'Multiple Ownership Claim'),
        ('encroachment', 'Encroachment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('submitted', 'Submitted to Land Officer'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    case_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Legal_case_id')
    case_land_record = models.ForeignKey(
        LandRecord,
        on_delete=models.CASCADE,
        related_name='legal_cases',
        db_column='Legal_case_land_record_id'
    )
    case_legal_officer = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='submitted_cases',
        db_column='Legal_case_legal_officer_id'
    )
    
    case_type = models.CharField(max_length=50, choices=CASE_TYPES, db_column='Legal_case_type')
    case_title = models.CharField(max_length=255, db_column='Legal_case_title')
    case_description = models.TextField(db_column='Legal_case_description')
    case_priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        default='medium',
        db_column='Legal_case_priority'
    )
    case_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', db_column='Legal_case_status')
    case_land_officer_notes = models.TextField(null=True, blank=True, db_column='Legal_case_land_officer_notes')
    case_created_at = models.DateTimeField(auto_now_add=True, db_column='Legal_case_created_at')
    case_updated_at = models.DateTimeField(auto_now=True, db_column='Legal_case_updated_at')

    class Meta:
        db_table = 'Legal_case'
        ordering = ['-case_created_at']

    def __str__(self):
        return f"{self.case_title} - {self.case_land_record.land_records_parcel_number}"

    def save(self, *args, **kwargs):
        if self.case_status == 'submitted' and not self.case_land_record.land_records_verification_status == 'flagged':
            self.case_land_record.land_records_verification_status = 'flagged'
            self.case_land_record.save()
        
        super().save(*args, **kwargs)
        
        
## =========================
# OWNERSHIP HISTORY TABLE
# =========================
class OwnershipHistory(models.Model):
    TRANSFER_TYPES = [
        ('sale', 'Sale'),
        ('transfer', 'Transfer'),
        ('inheritance', 'Inheritance'),
        ('gift', 'Gift'),
    ]

    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='Ownership_history_id')
    history_land_record = models.ForeignKey(
        LandRecord,
        on_delete=models.CASCADE,
        related_name='ownership_history',
        db_column='Ownership_history_land_record_id'
    )
    history_previous_owner = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transferred_from',
        db_column='Ownership_history_previous_owner_id'
    )
    history_new_owner = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transferred_to',
        db_column='Ownership_history_new_owner_id'
    )
    history_transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, db_column='Ownership_history_transfer_type')
    history_transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ownership_changes',
        db_column='Ownership_history_transaction_id'
    )
    history_deed_number_old = models.CharField(max_length=100, db_column='Ownership_history_old_deed_number')
    history_deed_number_new = models.CharField(max_length=100, db_column='Ownership_history_new_deed_number')
    history_transfer_date = models.DateTimeField(auto_now_add=True, db_column='Ownership_history_transfer_date')
    history_notes = models.TextField(null=True, blank=True, db_column='Ownership_history_notes')

    class Meta:
        db_table = 'Ownership_history'
        ordering = ['-history_transfer_date']

    def __str__(self):
        return f"Transfer: {self.history_land_record.land_records_parcel_number} - {self.history_transfer_date}"