from django.contrib import admin
from .models import UserProfile, LandRecord, Document, Transaction, Notification, LegalCaseSubmission, OwnershipHistory


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'user_email', 'user_role', 'user_county', 'user_id_number', 'user_phone_number', 'user_created_at'] 
    list_filter = ['user_role', 'user_county', 'user_created_at', 'user_email_verified']  
    search_fields = ['user_full_name', 'user_email', 'user_id_number', 'user_phone_number', 'user_county']  
    readonly_fields = ['user_id', 'user_created_at', 'user_updated_at', 'user_email_otp_created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_id', 'user_email', 'user_full_name', 'user_role', 'user_county')  
        }),
        ('Contact Details', {
            'fields': ('user_phone_number', 'user_id_number')
        }),
        ('Email Verification', {
            'fields': ('user_email_verified', 'user_email_otp', 'user_email_otp_created_at')
        }),
        ('Account Status', {
            'fields': ('user_is_active', 'is_staff', 'is_superuser', 'user_first_login_completed')
        }),
        ('Timestamps', {
            'fields': ('user_created_at', 'user_updated_at')
        }),
    )


@admin.register(LandRecord)
class LandRecordAdmin(admin.ModelAdmin):
    list_display = ['land_records_parcel_number', 'land_records_deed_number', 'land_records_owner_id', 'land_records_county', 'land_records_location', 'land_records_size', 'land_records_verification_status', 'land_records_created_at']  # NEW: Added land_records_county
    list_filter = ['land_records_verification_status', 'land_records_county', 'land_records_created_at']  
    search_fields = ['land_records_parcel_number', 'land_records_deed_number', 'land_records_location', 'land_records_county']  
    readonly_fields = ['land_records_id', 'land_records_registered_date', 'land_records_created_at', 'land_records_updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('land_records_id', 'land_records_parcel_number', 'land_records_deed_number', 'land_records_county')  
        }),
        ('Ownership', {
            'fields': ('land_records_owner_id', 'land_records_previous_owner')
        }),
        ('Location', {
            'fields': ('land_records_location', 'land_records_size')
        }),
        ('Verification', {
            'fields': ('land_records_verification_status',)
        }),
        ('Transfer Information', {
            'fields': ('land_records_transfer_date',)
        }),
        ('Timestamps', {
            'fields': ('land_records_registered_date', 'land_records_created_at', 'land_records_updated_at')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_land_record_id', 'transaction_from_owner_id', 'transaction_to_owner_id', 'transaction_county', 'transaction_type', 'transaction_amount', 'transaction_payment_status', 'transaction_legal_approval_status', 'transaction_created_at']  # NEW: Added transaction_county
    list_filter = ['transaction_type', 'transaction_payment_status', 'transaction_legal_approval_status', 'transaction_county', 'transaction_created_at'] 
    search_fields = ['transaction_land_record_id__land_records_parcel_number', 'transaction_payment_reference', 'transaction_county']  
    readonly_fields = ['transaction_id', 'transaction_created_at', 'transaction_approved_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction_id', 'transaction_land_record_id', 'transaction_type', 'transaction_county')  
        }),
        ('Parties', {
            'fields': ('transaction_from_owner_id', 'transaction_to_owner_id', 'transaction_to_owner_id_number')
        }),
        ('Payment', {
            'fields': ('transaction_amount', 'transaction_payment_reference', 'transaction_payment_status')
        }),
        ('Officer Assignment', {
            'fields': ('transaction_legal_officer_id', 'transaction_land_officer_id')
        }),
        ('Commissions', {
            'fields': ('transaction_legal_officer_share', 'transaction_land_officer_share')
        }),
        ('Legal Approval', {
            'fields': ('transaction_legal_approval_status', 'transaction_legal_notes', 'transaction_approved_at')
        }),
        ('Transfer Status', {
            'fields': ('transaction_transfer_completed', 'transaction_new_deed_number')
        }),
        ('Timestamps', {
            'fields': ('transaction_created_at',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_file_name', 'document_land_records_id', 'document_uploaded_by', 'document_status', 'document_created_at']
    list_filter = ['document_status', 'document_created_at']
    search_fields = ['document_file_name', 'document_land_records_id__land_records_parcel_number']
    readonly_fields = ['document_id', 'document_created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document_id', 'document_land_records_id', 'document_uploaded_by')
        }),
        ('File Details', {
            'fields': ('document_file_url', 'document_file_name', 'document_file_type')
        }),
        ('OCR Results', {
            'fields': ('document_ocr_text', 'document_ocr_metadata')
        }),
        ('Verification', {
            'fields': ('document_status', 'document_verification_notes')
        }),
        ('Timestamps', {
            'fields': ('document_created_at',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_title', 'notification_user_id', 'notification_type', 'notification_read', 'notification_created_at']
    list_filter = ['notification_type', 'notification_read', 'notification_created_at']
    search_fields = ['notification_title', 'notification_message', 'notification_user_id__user_full_name']
    readonly_fields = ['notification_id', 'notification_created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification_id', 'notification_user_id', 'notification_title', 'notification_message', 'notification_type')
        }),
        ('Related Entity', {
            'fields': ('notification_related_entity_type', 'notification_related_entity_id')
        }),
        ('Status', {
            'fields': ('notification_read',)
        }),
        ('Timestamps', {
            'fields': ('notification_created_at',)
        }),
    )


@admin.register(LegalCaseSubmission)
class LegalCaseSubmissionAdmin(admin.ModelAdmin):
    list_display = ['case_title', 'case_land_record', 'case_legal_officer', 'case_type', 'case_priority', 'case_status', 'case_created_at']
    list_filter = ['case_type', 'case_priority', 'case_status', 'case_created_at']
    search_fields = ['case_title', 'case_land_record__land_records_parcel_number']


@admin.register(OwnershipHistory)
class OwnershipHistoryAdmin(admin.ModelAdmin):
    list_display = ['history_land_record', 'history_previous_owner', 'history_new_owner', 'history_transfer_type', 'history_transfer_date']
    list_filter = ['history_transfer_type', 'history_transfer_date']
    search_fields = ['history_land_record__land_records_parcel_number']