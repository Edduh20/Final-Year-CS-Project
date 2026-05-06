from rest_framework import serializers
from .models import (
    UserProfile, LandRecord, Document, Transaction,
    Notification,  OwnershipHistory, LegalCaseSubmission
)

# ---------------------------------------------------------------------------
# USER PROFILE SERIALIZER
# ---------------------------------------------------------------------------

class UserProfileSerializer(serializers.ModelSerializer):
    """Maps actual DB fields to clean API field names"""
    id = serializers.UUIDField(source='user_id', read_only=True)
    email = serializers.EmailField(source='user_email')
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.CharField(source='user_role')
    full_name = serializers.CharField(source='user_full_name')
    phone_number = serializers.CharField(source='user_phone_number', allow_null=True, required=False, allow_blank=True)
    id_number = serializers.CharField(source='user_id_number', allow_null=True, required=False, allow_blank=True)
    county = serializers.CharField(source='user_county', allow_null=True, required=False, allow_blank=True)
    is_active = serializers.BooleanField(source='user_is_active', read_only=True)
    email_verified = serializers.BooleanField(source='user_email_verified', read_only=True)
    first_login_completed = serializers.BooleanField(source='user_first_login_completed', read_only=True)
    created_at = serializers.DateTimeField(source='user_created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='user_updated_at', read_only=True)
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'password', 'role', 'full_name', 'phone_number',
            'id_number', 'county', 'is_active', 'email_verified', 'first_login_completed',
            'created_at', 'updated_at', 'current_password', 'new_password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Password is required'})

        user = UserProfile.objects.create_user(
            user_email=validated_data['user_email'],
            password=password,
            user_full_name=validated_data.get('user_full_name', ''),
            user_role=validated_data.get('user_role', 'user'),
            user_phone_number=validated_data.get('user_phone_number'),
            user_id_number=validated_data.get('user_id_number'),
            user_county=validated_data.get('user_county'), 
        )
        return user

    def update(self, instance, validated_data):
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)

        # 🔐 Handle password change properly
        if new_password:
            if not current_password:
                raise serializers.ValidationError({
                    "current_password": "Current password is required"
                })

            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    "current_password": "Incorrect password"
                })

            instance.set_password(new_password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


# ---------------------------------------------------------------------------
# LAND RECORD SERIALIZERS 
# ---------------------------------------------------------------------------
class LandRecordListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='land_records_id', read_only=True)
    parcel_number = serializers.CharField(source='land_records_parcel_number')
    deed_number = serializers.CharField(source='land_records_deed_number')
    owner = UserProfileSerializer(source='land_records_owner_id', read_only=True)
    previous_owner = UserProfileSerializer(source='land_records_previous_owner', read_only=True)  
    location = serializers.CharField(source='land_records_location')
    county = serializers.CharField(source='land_records_county')
    size_hectares = serializers.DecimalField(source='land_records_size', max_digits=10, decimal_places=2)
    status = serializers.CharField(source='land_records_verification_status')
    transfer_date = serializers.DateTimeField(source='land_records_transfer_date', read_only=True)  
    has_legal_case = serializers.SerializerMethodField()
    legal_case_description = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='land_records_created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='land_records_updated_at', read_only=True)

    class Meta:
        model = LandRecord
        fields = [
            'id', 'parcel_number', 'deed_number', 'owner', 'previous_owner', 'location', 'county',
            'size_hectares', 'status', 'transfer_date',
            'has_legal_case', 'legal_case_description', 'created_at', 'updated_at'
        ]

    def get_has_legal_case(self, obj):
        return False

    def get_legal_case_description(self, obj):
        return None


class OwnershipHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='history_id', read_only=True)
    land_record = serializers.UUIDField(source='history_land_record.land_records_id', read_only=True)
    parcel_number = serializers.SerializerMethodField()
    
    previous_owner = UserProfileSerializer(source='history_previous_owner', read_only=True)
    new_owner = UserProfileSerializer(source='history_new_owner', read_only=True)

    previous_owner_name = serializers.CharField(source='history_previous_owner.user_full_name', read_only=True)
    new_owner_name = serializers.CharField(source='history_new_owner.user_full_name', read_only=True)

    transfer_type = serializers.CharField(source='history_transfer_type')
    old_deed_number = serializers.CharField(source='history_deed_number_old')
    new_deed_number = serializers.CharField(source='history_deed_number_new')
    transfer_date = serializers.DateTimeField(source='history_transfer_date', read_only=True)
    notes = serializers.CharField(source='history_notes', read_only=True)

    class Meta:
        model = OwnershipHistory
        fields = [
            'id',
            'land_record',
            "parcel_number",
            'previous_owner', 'new_owner',
            'previous_owner_name', 'new_owner_name',
            'transfer_type',
            'old_deed_number', 'new_deed_number',
            'transfer_date',
            'notes'
        ]
    
    def get_parcel_number(self, obj):
        if obj.history_land_record:
            return obj.history_land_record.land_records_parcel_number
        return None



class LandRecordDetailSerializer(LandRecordListSerializer):
    """Detailed view for land records"""
    pass



class LandRecordCreateSerializer(serializers.ModelSerializer):
    parcel_number = serializers.CharField(source='land_records_parcel_number')
    deed_number = serializers.CharField(source='land_records_deed_number')
    owner_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    id_number = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(source='land_records_location')
    county = serializers.CharField(source='land_records_county', required=False, allow_blank=True)
    size_hectares = serializers.DecimalField(source='land_records_size', max_digits=10, decimal_places=2)

    class Meta:
        model = LandRecord
        fields = [
            'parcel_number', 'deed_number', 'owner_id', 'id_number',
            'location', 'county', 'size_hectares'
        ]

    def create(self, validated_data):
        owner = None

        owner_uuid = self.initial_data.get("owner_id")
        if owner_uuid:
            try:
                owner = UserProfile.objects.get(user_id=owner_uuid)
            except UserProfile.DoesNotExist:
                print(f" No user found for UUID: {owner_uuid}")

        if not owner:
            id_number = self.initial_data.get("id_number")
            if id_number and id_number.strip():
                try:
                    owner = UserProfile.objects.get(user_id_number=id_number.strip())
                except UserProfile.DoesNotExist:
                    print(f" No user found for ID number: {id_number}")

        record = LandRecord.objects.create(
            land_records_parcel_number=validated_data["land_records_parcel_number"],
            land_records_deed_number=validated_data["land_records_deed_number"],
            land_records_location=validated_data["land_records_location"],
            land_records_county=validated_data.get("land_records_county", ""),
            land_records_size=validated_data["land_records_size"],
            land_records_owner_id=owner,  
            land_records_verification_status='pending'
        )

        if owner:
            print(f" Land record created and linked to {owner.user_full_name}")
        else:
            print(f" Land record created without owner (will auto-link when user registers)")

        return record



# ---------------------------------------------------------------------------
# DOCUMENT SERIALIZERS 
# ---------------------------------------------------------------------------
class DocumentCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    parcel_number = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Document
        fields = [
            'parcel_number',
            'document_file_name',
            'document_file_type',
            'file',
        ]

    def create(self, validated_data):
        parcel_number = validated_data.pop('parcel_number', None)
        file = validated_data.pop('file')
        request_user = self.context['request'].user

        from django.core.files.storage import default_storage
        path = default_storage.save(f"documents/{file.name}", file)

        land_record = None
        if parcel_number:
            try:
                land_record = LandRecord.objects.get(land_records_parcel_number=parcel_number)
            except LandRecord.DoesNotExist:
                print(f" No land record found for parcel: {parcel_number}")


        document = Document.objects.create(
            document_land_records_id=land_record,  
            document_uploaded_by=request_user,
            document_file_name=validated_data.get('document_file_name', file.name),
            document_file_type=validated_data.get('document_file_type', 'unknown'),
            document_file_url=path, 
            document_status='pending_payment'
        )
        
        
        return document


class DocumentListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='document_id', read_only=True)
    
    land_record = serializers.SerializerMethodField()
    
    uploaded_by = serializers.SerializerMethodField()
    
    file_url = serializers.CharField(source='document_file_url')
    file_name = serializers.CharField(source='document_file_name')
    file_type = serializers.CharField(source='document_file_type')
    status = serializers.CharField(source='document_status')
    ocr_metadata = serializers.JSONField(source='document_ocr_metadata', allow_null=True, required=False)
    
    verification_notes = serializers.CharField(
        source='document_verification_notes', 
        allow_null=True, 
        required=False
    )
    
    created_at = serializers.DateTimeField(source='document_created_at', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'land_record', 'uploaded_by', 'file_url', 'file_name', 
            'file_type', 'status', 'verification_notes', 'ocr_metadata',
            'created_at'
        ]
    
    def get_land_record(self, obj):
        if obj.document_land_records_id:
            return {
                'land_records_id': obj.document_land_records_id.land_records_id,
                'land_records_parcel_number': obj.document_land_records_id.land_records_parcel_number,
                'land_records_deed_number': obj.document_land_records_id.land_records_deed_number,
                'land_records_location': obj.document_land_records_id.land_records_location,
            }
        return None
    
    def get_uploaded_by(self, obj):
        if obj.document_uploaded_by:
            return {
                'user_id': obj.document_uploaded_by.user_id,
                'user_full_name': obj.document_uploaded_by.user_full_name,
                'user_email': obj.document_uploaded_by.user_email,
            }
        return None


class DocumentDetailSerializer(DocumentListSerializer):
    verification_notes = serializers.CharField(source='document_verification_notes', read_only=True, allow_null=True)

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + [
            'verification_notes'
        ]


# ---------------------------------------------------------------------------
# TRANSACTION SERIALIZERS 
# ---------------------------------------------------------------------------

class TransactionListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='transaction_id', read_only=True)
    
    land_record = serializers.SerializerMethodField()
    from_owner = serializers.SerializerMethodField()
    to_owner = serializers.SerializerMethodField()
    
    to_owner_id_number = serializers.CharField(source='transaction_to_owner_id_number', read_only=True)
    
    transaction_type = serializers.CharField()
    transaction_amount = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    transaction_payment_status = serializers.CharField()
    transaction_legal_approval_status = serializers.CharField()
    transaction_payment_reference = serializers.CharField(allow_null=True)
    transaction_created_at = serializers.DateTimeField(read_only=True)
    
    legal_officer_commission = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    land_officer_commission = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    
    transaction_transfer_completed = serializers.BooleanField()
    transaction_new_deed_number = serializers.CharField(allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'land_record', 'from_owner', 'to_owner', 'to_owner_id_number',
            'transaction_type', 'transaction_amount', 'transaction_payment_status',
            'transaction_legal_approval_status', 'transaction_payment_reference',
            'transaction_created_at', 'legal_officer_commission', 'land_officer_commission',
            'transaction_transfer_completed', 'transaction_new_deed_number'
        ]

    def get_land_record(self, obj):
        land_record = obj.transaction_land_record_id
        if land_record:
            return {
                'land_records_id': land_record.land_records_id,
                'land_records_parcel_number': land_record.land_records_parcel_number,
                'land_records_deed_number': land_record.land_records_deed_number,
                'land_records_location': land_record.land_records_location,
                'land_records_size': float(land_record.land_records_size) if land_record.land_records_size else None,
                'land_records_verification_status': land_record.land_records_verification_status
            }
        return None

    def get_from_owner(self, obj):
        owner = obj.transaction_from_owner_id
        if owner:
            return {
                'user_id': owner.user_id,
                'user_full_name': owner.user_full_name,
                'user_email': owner.user_email,
                'user_phone_number': owner.user_phone_number,
                'user_id_number': owner.user_id_number
            }
        return None

    def get_to_owner(self, obj):
        to_owner = obj.transaction_to_owner_id
        
        if not to_owner and obj.transaction_to_owner_id_number:
            to_owner = obj.resolve_to_owner()  
        
        if to_owner:
            return {
                'user_id': to_owner.user_id,
                'user_full_name': to_owner.user_full_name,
                'user_email': to_owner.user_email,
                'user_phone_number': to_owner.user_phone_number,
                'user_id_number': to_owner.user_id_number
            }
        
        if obj.transaction_to_owner_id_number:
            return {
                'user_id_number': obj.transaction_to_owner_id_number,
                'user_full_name': 'Pending User Resolution',
                'user_email': 'N/A',
                'user_phone_number': 'N/A'
            }
        
        return None

class TransactionDetailSerializer(TransactionListSerializer):
    legal_notes = serializers.CharField(source='transaction_legal_notes', read_only=True, allow_null=True)
    legal_officer = serializers.SerializerMethodField()
    land_officer = serializers.SerializerMethodField()
    approved_at = serializers.DateTimeField(source='transaction_approved_at', allow_null=True)
    

    class Meta(TransactionListSerializer.Meta):
        fields = TransactionListSerializer.Meta.fields + [
            'legal_notes', 'legal_officer', 'land_officer', 'approved_at'
        ]

    def get_legal_officer(self, obj):
        if obj.transaction_legal_officer_id:
            return {
                'user_id': obj.transaction_legal_officer_id.user_id,
                'user_full_name': obj.transaction_legal_officer_id.user_full_name,
                'user_email': obj.transaction_legal_officer_id.user_email
            }
        return None

    def get_land_officer(self, obj):
        if obj.transaction_land_officer_id:
            return {
                'user_id': obj.transaction_land_officer_id.user_id,
                'user_full_name': obj.transaction_land_officer_id.user_full_name,
                'user_email': obj.transaction_land_officer_id.user_email
            }
        return None
            

# ---------------------------------------------------------------------------
# NOTIFICATION SERIALIZER 
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='notification_id', read_only=True)
    user = serializers.UUIDField(source='notification_user_id.user_id', read_only=True)
    title = serializers.CharField(source='notification_title')
    message = serializers.CharField(source='notification_message')
    type = serializers.CharField(source='notification_type')
    read = serializers.BooleanField(source='notification_read')
    created_at = serializers.DateTimeField(source='notification_created_at', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'type', 'read', 'created_at'
        ]



# ---------------------------------------------------------------------------
# HELPER SERIALIZERS
# ---------------------------------------------------------------------------

class StatisticsSerializer(serializers.Serializer):
    total_land_records = serializers.IntegerField()
    verified_records = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()
    flagged_records = serializers.IntegerField()
    pending_legal_approvals = serializers.IntegerField(required=False)
    total_users = serializers.IntegerField(required=False)
    recent_transactions = serializers.IntegerField()



class DocumentVerificationSerializer(serializers.Serializer):
    authenticity_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    verification_notes = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['verified', 'rejected'])


class TransactionCreateSerializer(serializers.Serializer):
    land_record_id = serializers.UUIDField()
    to_owner_id = serializers.UUIDField()
    transaction_type = serializers.ChoiceField(
        choices=['sale', 'transfer', 'inheritance', 'gift']
    )
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)


# ===================== M-PESA PAYMENT SERIALIZERS =====================

class PaymentInitiationSerializer(serializers.Serializer):
    """
    Serializer for initiating M-Pesa payment requests
    """
    phone_number = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class PaymentCallbackSerializer(serializers.Serializer):
    """
    Serializer for handling M-Pesa callback (STK Push responses)
    """
    Body = serializers.JSONField(required=False)

    def validate(self, data):
        body = data.get('Body', {})
        if not isinstance(body, dict) or 'stkCallback' not in body:
            raise serializers.ValidationError("Invalid M-Pesa callback format")
        return data
    
# =========================
# LEGAL CASE SERIALIZERS
# =========================
class LegalCaseSubmissionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='case_id', read_only=True)
    land_record = serializers.UUIDField(source='case_land_record.land_records_id', read_only=True)
    land_record_details = serializers.SerializerMethodField()
    legal_officer = UserProfileSerializer(source='case_legal_officer', read_only=True)
    title = serializers.CharField(source='case_title', read_only=True)
    description = serializers.CharField(source='case_description', read_only=True)
    evidence_document = serializers.UUIDField(source='case_evidence_document.document_id', read_only=True, allow_null=True)
    priority = serializers.CharField(source='case_priority', read_only=True)
    status = serializers.CharField(source='case_status', read_only=True)
    land_officer_notes = serializers.CharField(source='case_land_officer_notes', allow_null=True, read_only=True)
    created_at = serializers.DateTimeField(source='case_created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='case_updated_at', read_only=True)

    class Meta:
        model = LegalCaseSubmission
        fields = [
            'id', 'land_record', 'land_record_details', 'legal_officer', 'case_type', 
            'title', 'description', 'evidence_document', 'priority', 'status',
            'land_officer_notes', 'created_at', 'updated_at'
        ]

    def get_land_record_details(self, obj):
        return {
            'parcel_number': obj.case_land_record.land_records_parcel_number,
            'deed_number': obj.case_land_record.land_records_deed_number,
            'location': obj.case_land_record.land_records_location,
            'current_owner': obj.case_land_record.land_records_owner_id.user_full_name if obj.case_land_record.land_records_owner_id else 'N/A'
        }

class LegalCaseCreateSerializer(serializers.ModelSerializer):
    land_record_parcel = serializers.CharField(write_only=True)

    class Meta:
        model = LegalCaseSubmission
        fields = [
            'land_record_parcel', 'case_type', 'case_title', 'case_description',
            'case_priority'
        ]

    def create(self, validated_data):
        land_record_parcel = validated_data.pop('land_record_parcel')
        
        try:
            land_record = LandRecord.objects.get(land_records_parcel_number=land_record_parcel)
        except LandRecord.DoesNotExist:
            raise serializers.ValidationError({'land_record_parcel': 'Land record not found'})


        case = LegalCaseSubmission.objects.create(
            case_land_record=land_record,
            case_legal_officer=self.context['request'].user,
            **validated_data
        )

        legal_officer_county = self.context['request'].user.user_county
        land_officers = UserProfile.objects.filter(
            user_role='land_officer',
            user_county=legal_officer_county,
            user_is_active=True
        )
        
        for officer in land_officers:
            Notification.objects.create(
                notification_user_id=officer,
                notification_title='New Legal Case Submitted',
                notification_message=f'Legal case "{case.case_title}" submitted for parcel {land_record.land_records_parcel_number}. Priority: {case.case_priority}',
                notification_type='warning',
                notification_related_entity_type='legal_case',
                notification_related_entity_id=case.case_id
            )

        return case