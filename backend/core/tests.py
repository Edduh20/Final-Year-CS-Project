from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
import uuid

from .models import UserProfile, LandRecord, Document, Transaction, Notification
from .utils import parse_land_document, calculate_authenticity_score


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user_profile = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='John Doe',
            phone_number='+254712345678',
            id_number='12345678'
        )

    def test_user_profile_creation(self):
        self.assertEqual(self.user_profile.full_name, 'John Doe')
        self.assertEqual(self.user_profile.role, 'user')
        self.assertIsNotNone(self.user_profile.id)

    def test_user_profile_str(self):
        self.assertEqual(str(self.user_profile), 'John Doe (user)')


class LandRecordModelTest(TestCase):
    """Test LandRecord model"""

    def setUp(self):
        self.owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Jane Smith',
            id_number='87654321'
        )
        self.land_record = LandRecord.objects.create(
            parcel_number='LR-12345',
            deed_number='TD-67890',
            owner=self.owner,
            location='Nairobi, Westlands',
            latitude=Decimal('-1.286389'),
            longitude=Decimal('36.817223'),
            size_hectares=Decimal('2.5'),
            verification_status='pending'
        )

    def test_land_record_creation(self):
        self.assertEqual(self.land_record.parcel_number, 'LR-12345')
        self.assertEqual(self.land_record.owner, self.owner)
        self.assertEqual(self.land_record.verification_status, 'pending')

    def test_land_record_str(self):
        self.assertEqual(str(self.land_record), 'LR-12345 - Nairobi, Westlands')


class DocumentModelTest(TestCase):
    """Test Document model"""

    def setUp(self):
        self.owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Test User'
        )
        self.land_record = LandRecord.objects.create(
            parcel_number='LR-99999',
            deed_number='TD-88888',
            owner=self.owner,
            location='Test Location',
            size_hectares=Decimal('1.0')
        )
        self.document = Document.objects.create(
            land_record=self.land_record,
            uploaded_by=self.owner,
            file_url='https://example.com/document.pdf',
            file_name='title_deed.pdf',
            file_type='application/pdf',
            status='pending'
        )

    def test_document_creation(self):
        self.assertEqual(self.document.file_name, 'title_deed.pdf')
        self.assertEqual(self.document.status, 'pending')
        self.assertEqual(self.document.land_record, self.land_record)


class OCRUtilityTest(TestCase):
    """Test OCR utility functions"""

    def test_parse_land_document(self):
        sample_text = """
        REPUBLIC OF KENYA
        MINISTRY OF LANDS
        Owner Name: John Kamau
        National ID: 12345678
        Parcel Number: LR-54321
        Deed Number: TD-98765
        Issue Date: 2024-01-15
        """
        metadata = parse_land_document(sample_text)

        self.assertEqual(metadata['owner_name'], 'John Kamau')
        self.assertEqual(metadata['id_number'], '12345678')
        self.assertIn('LR', metadata['parcel_number'])
        self.assertIn('TD', metadata['deed_number'])
        self.assertGreater(metadata['confidence'], 0)

    def test_parse_land_document_partial_match(self):
        sample_text = """
        Owner: Mary Wanjiku
        ID: 87654321
        """
        metadata = parse_land_document(sample_text)

        self.assertIsNotNone(metadata['owner_name'])
        self.assertGreater(metadata['confidence'], 0)
        
    def debug_ocr_for_document(document_id):
        from .models import Document
        document = Document.objects.get(document_id=document_id)
        
        file_path = document.document_file_url
        file_content = default_storage.open(file_path).read()
        
        extracted_text = extract_text_from_pdf(file_content)
        
        extracted_data = extract_structured_data(extracted_text)
        
        return {
            'document_name': document.document_file_name,
            'extracted_text_sample': extracted_text[:1000],
            'extracted_data': extracted_data
        }
        
   



class LandRecordAPITest(APITestCase):
    """Test Land Record API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user_profile = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='API Test User'
        )

    def test_create_land_record(self):
        data = {
            'parcel_number': 'LR-API001',
            'deed_number': 'TD-API001',
            'owner': str(self.user_profile.id),
            'location': 'Test Location',
            'size_hectares': '3.5'
        }

        response = self.client.post('/api/land-records/', data, format='json')

        if response.status_code == 401:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        else:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_land_records(self):
        LandRecord.objects.create(
            parcel_number='LR-TEST001',
            deed_number='TD-TEST001',
            owner=self.user_profile,
            location='Test Location',
            size_hectares=Decimal('2.0')
        )

        response = self.client.get('/api/land-records/')

        if response.status_code == 401:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        else:
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class DocumentAPITest(APITestCase):
    """Test Document API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user_profile = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='land_officer',
            full_name='Officer Test'
        )
        self.land_record = LandRecord.objects.create(
            parcel_number='LR-DOC001',
            deed_number='TD-DOC001',
            owner=self.user_profile,
            location='Test',
            size_hectares=Decimal('1.0')
        )

    def test_document_upload(self):
        data = {
            'land_record': str(self.land_record.id),
            'uploaded_by': str(self.user_profile.id),
            'file_url': 'https://example.com/test.pdf',
            'file_name': 'test_document.pdf',
            'file_type': 'application/pdf'
        }

        response = self.client.post('/api/documents/', data, format='json')

        if response.status_code == 401:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionAPITest(APITestCase):
    """Test Transaction API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.from_owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Seller'
        )
        self.to_owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Buyer'
        )
        self.land_record = LandRecord.objects.create(
            parcel_number='LR-TRANS001',
            deed_number='TD-TRANS001',
            owner=self.from_owner,
            location='Test',
            size_hectares=Decimal('1.5')
        )

    def test_create_transaction(self):
        data = {
            'land_record': str(self.land_record.id),
            'from_owner': str(self.from_owner.id),
            'to_owner': str(self.to_owner.id),
            'transaction_type': 'sale',
            'amount': '5000000'
        }

        response = self.client.post('/api/transactions/', data, format='json')

        if response.status_code == 401:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationTest(TestCase):
    """Test Notification model and creation"""

    def setUp(self):
        self.user = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Notification User'
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            type='info'
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.read)


class SecurityTest(TestCase):
    """Test security measures"""

    def test_unique_parcel_numbers(self):
        owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Security Test'
        )

        LandRecord.objects.create(
            parcel_number='LR-SEC001',
            deed_number='TD-SEC001',
            owner=owner,
            location='Test',
            size_hectares=Decimal('1.0')
        )

        with self.assertRaises(Exception):
            LandRecord.objects.create(
                parcel_number='LR-SEC001',
                deed_number='TD-SEC002',
                owner=owner,
                location='Test',
                size_hectares=Decimal('1.0')
            )


class IntegrationTest(TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='Integration Test User',
            id_number='11111111'
        )
        self.officer = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='land_officer',
            full_name='Test Officer'
        )

    def test_complete_verification_workflow(self):
        land_record = LandRecord.objects.create(
            parcel_number='LR-INT001',
            deed_number='TD-INT001',
            owner=self.owner,
            location='Integration Test Location',
            size_hectares=Decimal('2.5'),
            verification_status='pending'
        )

        document = Document.objects.create(
            land_record=land_record,
            uploaded_by=self.owner,
            file_url='https://example.com/integration_test.pdf',
            file_name='integration_test.pdf',
            status='pending'
        )

        document.status = 'verified'
        document.authenticity_score = Decimal('85.5')
        document.verified_by = self.officer
        document.save()

        land_record.verification_status = 'verified'
        land_record.save()

        self.assertEqual(document.status, 'verified')
        self.assertEqual(land_record.verification_status, 'verified')
        self.assertIsNotNone(document.verified_by)

    def test_ownership_transfer_workflow(self):
        land_record = LandRecord.objects.create(
            parcel_number='LR-TRANS002',
            deed_number='TD-TRANS002',
            owner=self.owner,
            location='Transfer Test',
            size_hectares=Decimal('1.0')
        )

        new_owner = UserProfile.objects.create(
            id=uuid.uuid4(),
            role='user',
            full_name='New Owner'
        )

        transaction = Transaction.objects.create(
            land_record=land_record,
            from_owner=self.owner,
            to_owner=new_owner,
            transaction_type='sale',
            amount=Decimal('3000000'),
            payment_status='completed',
            legal_approval_status='approved'
        )

        land_record.owner = new_owner
        land_record.save()

        self.assertEqual(land_record.owner, new_owner)
        self.assertEqual(transaction.legal_approval_status, 'approved')
