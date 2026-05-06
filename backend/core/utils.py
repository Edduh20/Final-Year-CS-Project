import os
import re
import uuid
import base64
import requests
from datetime import datetime
from PIL import Image, ImageEnhance
from decimal import Decimal
import PyPDF2
import io
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from decouple import config

from .models import Document, Notification, UserProfile, LandRecord, Transaction, OwnershipHistory

# ==================== OCR & PDF PROCESSING ====================#

def extract_text_from_pdf(pdf_content):
    """1. Extract text from PDF file"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception("Failed to extract text from PDF")

def preprocess_image(image):
    """2. Preprocess image for better OCR results"""
    if image.mode != 'L':
        image = image.convert('L')  
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  
    
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)
    
    if image.size[0] < 600:
        new_width = 1200
        ratio = new_width / float(image.size[0])
        new_height = int(float(image.size[1]) * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image



def extract_text_from_image(image_content):
    """3. Extract text from image using OCR API"""
    try:
        import base64
        import os
        import requests

        api_key = os.getenv("OCR_API_KEY")
        if not api_key:
            raise Exception("OCR_API_KEY is missing in environment variables")

        base64_image = base64.b64encode(image_content).decode("utf-8")

        url = "https://api.ocr.space/parse/image"

        payload = {
            "base64Image": f"data:image/jpeg;base64,{base64_image}",
            "apikey": api_key,
            "language": "eng"
        }

        response = requests.post(url, data=payload, timeout=15)
        result = response.json()

        if result.get("IsErroredOnProcessing"):
            raise Exception(result.get("ErrorMessage"))

        parsed_results = result.get("ParsedResults")
        if not parsed_results:
            raise Exception("No text found in image")

        text = parsed_results[0].get("ParsedText", "")

        return text.strip()

    except Exception as e:
        raise Exception(f"OCR API failed: {str(e)}")

def extract_structured_data(text):
    """4. Extract structured property data from OCR text"""
    extracted_data = {}
    
    if not text or len(text.strip()) < 10:
        return extracted_data
    
    extracted_data = extract_from_official_deed_format(text)
    
    if 'parcel_number' not in extracted_data or not extracted_data['parcel_number']:
        print("DEBUG: Parcel number not found, using special extractor...")
        special_parcel = extract_parcel_from_problematic_ocr(text)
        if special_parcel:
            extracted_data['parcel_number'] = special_parcel
            print(f"DEBUG: Special extraction found parcel: {special_parcel}")
    
    extracted_data = clean_extracted_data(extracted_data)
    
    return extracted_data

def extract_from_official_deed_format(text):
    """5a. Extract data from the new official deed format"""
    data = {}
    
    patterns = {
        'parcel_number': [
            r'Title\s*Number\s*:\s*(LR[^,\n\s]{15,})', 
            r'Title\s*Number\s*:\s*(LR[/_\-A-Z0-9]+)', 
            r'Parcel\s*Number\s*:\s*(LR[^,\n\s]{15,})',  
            r'Parcel\s*Number\s*:\s*(LR[/_\-A-Z0-9]+)', 
            r'LR[/_\-A-Z0-9]{10,}',  
        ],
        'deed_number': [
            r'Deed\s*Number\s*:\s*(TD[^,\n\s]+)',  
            r'Deed\s*Number\s*:\s*(DE?ED?[/_\-A-Z0-9]+)', 
            r'TD[/_\-A-Z0-9]+', 
        ],
        'owner_full_name': [
            r'This\s+is\s+to\s+certify\s+that\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+of\s+ID',  
            r'certify\s+that\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+of\s+ID',  
        ],
        'owner_id_number': [
            r'ID\s+No\.?\s*\.?\s*(\d{8})', 
            r'ID\s*Number\s*:\s*(\d{8})',  
            r'(\d{8})',  
        ],
        'land_size': [
            r'Approximate\s+Area\s*:\s*([\d\.]+)\s*Ha\.?', 
            r'Area\s*:\s*([\d\.]+)\s*Ha\.?',  
        ],
        'location': [
            r'GIVEN.*\s+of\s+the\s+([A-Z]+)\s+District',  
            r'([A-Z]+)\s+District\s+Land\s+Registry', 
        ],
        'registration_date': [
            r'this\s+(\d+)\s+day\s+of\s+([A-Za-z]+),\s+(\d{4})', 
        ],
        'land_registrar': [
            r'Name:\s*([A-Za-z\s]+Land Registrar)',  
            r'Land\s+Registrar:\s*([A-Za-z\s]+)',  
        ]
    }
    
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                if match.groups():
                    if field == 'registration_date' and len(match.groups()) == 3:
                        day, month, year = match.groups()
                        data[field] = f"{day} {month} {year}"
                    else:
                        data[field] = match.group(1).strip()
                else:
                    data[field] = match.group(0).strip()
                print(f"DEBUG: Matched {field}: {data[field]}")  
                break  
    
    return data

def correct_ocr_letter_errors(text):
    """Correct common OCR letter confusions"""
    if not text:
        return text
    

    corrections = {
        'V': 'I',    
        'W': 'U',    
        'VV': 'W',   
        'II': 'U',  
        '0': 'O',   
        '1': 'I',   
        '5': 'S',   
        '8': 'B',    
        'G': '6',    
        '6': 'G',    
    }
    
    result = text.upper()
    
    for wrong, correct in corrections.items():
        if wrong in result:
            result = result.replace(wrong, correct)
    
    return result

def normalize_county_name_with_ocr_correction(county_text):
    """Normalize county names with OCR error correction"""
    if not county_text:
        return county_text
    

    corrected = correct_ocr_letter_errors(county_text)
    

    return normalize_county_name(corrected)

def clean_extracted_data(data):
    """6. Clean up extracted OCR data - with OCR error correction"""
    cleaned_data = {}
    
    for key, value in data.items():
        if value:
            value = ' '.join(value.split()) 
            
            if key == 'parcel_number':
                value = value.upper()
                value = value.replace(' ', '')
                
                print(f"DEBUG: Raw parcel number: {value}")  
                

                if value.startswith('LRI'):
                    value = 'LR/' + value[3:]
                

                if '/' in value:
                    parts = value.split('/')
                    if len(parts) >= 2:
                        corrected_county = correct_ocr_letter_errors(parts[1])
                        parts[1] = corrected_county
                        value = '/'.join(parts)
                

                if '/' in value:
                    parts = value.split('/')
                    if len(parts) >= 2:
                        county = normalize_county_name(parts[1])
                        parts[1] = county
                        cleaned_data[key] = '/'.join(parts)
                    else:
                        cleaned_data[key] = value
                else:
                    cleaned_data[key] = value
                
                print(f"DEBUG: Cleaned parcel number: {cleaned_data.get(key)}")  
                    
            elif key == 'deed_number':
                value = value.upper().replace(' ', '')
                print(f"DEBUG: Raw deed number: {value}")
                

                if '/' in value:
                    parts = value.split('/')
                    if len(parts) >= 2:

                        corrected_county = correct_ocr_letter_errors(parts[1])
                        parts[1] = corrected_county
                        value = '/'.join(parts)
                

                if '/' in value:
                    parts = value.split('/')
                    if len(parts) >= 2:
                        county = normalize_county_name(parts[1])
                        parts[1] = county
                        cleaned_data[key] = '/'.join(parts)
                    else:
                        cleaned_data[key] = value
                else:
                    cleaned_data[key] = value
                
                print(f"DEBUG: Cleaned deed number: {cleaned_data.get(key)}")
                
            elif key == 'owner_full_name':
                value = value.replace('of ID', '').strip()
                words = value.split()
                cleaned_words = []
                for word in words:
                    if word.isupper() and len(word) > 1:
                        cleaned_words.append(word)
                    else:
                        cleaned_words.append(word.title())
                value = ' '.join(cleaned_words)
                cleaned_data[key] = value
                
            elif key == 'owner_id_number':
                value = re.sub(r'[^0-9]', '', value)
                cleaned_data[key] = value
                
            elif key == 'land_size':
                value = re.sub(r'[^\d\.]', '', value)
                cleaned_data[key] = value
                
            elif key == 'location':
                value = value.replace('District', '').strip().upper()
                corrected = correct_ocr_letter_errors(value)
                county = normalize_county_name(corrected)
                cleaned_data[key] = county
                
            else:
                cleaned_data[key] = value
    
    return cleaned_data

def smart_ocr_correction(text, context='county'):
    """Smart OCR correction based on context"""
    if not text:
        return text
    
    text = text.upper()
    

    county_patterns = {
        'MIGORV': 'MIGORI',    
        'MIGORW': 'MIGORI',    
        'MIGORU': 'MIGORI',   
        'MIGOR1': 'MIGORI',   
        'MIGORL': 'MIGORI',    
        'MIGOR': 'MIGORI',     
        'NAIROB1': 'NAIROBI',  
        'NAIROBL': 'NAIROBI', 
        'KISUMV': 'KISUMU',    
        'KISUMW': 'KISUMU',   
        'KISUM': 'KISUMU',     
        'MOMBASA1': 'MOMBASA', 
        'MOMBASV': 'MOMBASA',  
        'TAITAV': 'TAITA_TAVETA', 
        'HOMAV': 'HOMA_BAY',   
    }
    

    for wrong, correct in county_patterns.items():
        if wrong in text:
            return correct
    

    corrections = {
        'V': 'I', 'W': 'U', '0': 'O', '1': 'I', 
        '5': 'S', '8': 'B', 'G': '6', '6': 'G',
        'VV': 'W', 'II': 'U', 'LL': 'U',
    }
    
    result = text
    for wrong, correct in corrections.items():
        if wrong in result:
            result = result.replace(wrong, correct)
    
    return result

def normalize_county_name_with_ocr_correction(county_text):
    """Normalize county names with smart OCR error correction"""
    if not county_text:
        return county_text
    

    corrected = smart_ocr_correction(county_text, context='county')
    

    return normalize_county_name(corrected)

def extract_parcel_from_problematic_ocr(text):
    """
    Special function to extract parcel number when standard patterns fail
    """
    title_line = None
    for line in text.split('\n'):
        if 'Title Number:' in line or 'Parcel Number:' in line:
            title_line = line
            break
    
    if not title_line:
        return None
    
    print(f"DEBUG: Found title line: {title_line}")
    
    if ':' in title_line:
        value = title_line.split(':', 1)[1].strip()
        print(f"DEBUG: Raw value after colon: {value}")
        
        value = value.upper()
        value = re.sub(r'[^A-Z0-9/]', '', value)  
        
        if value.startswith('LRI'):
            value = 'LR/' + value[3:]
        
        county = extract_county_from_parcel(value)
        
        numbers = re.findall(r'\d+', value)
        
        if county and county != 'nairobi' and len(numbers) >= 2:
            return f"LR/{county.upper()}/{numbers[0]}/{numbers[1]}"
        elif len(numbers) >= 2:
            county_match = re.search(r'LR/?([A-Z]+)', value)
            if county_match:
                county_name = county_match.group(1)
                county = extract_county_from_parcel(f"LR/{county_name}/0/0")
                if county and county != 'nairobi':
                    return f"LR/{county.upper()}/{numbers[0]}/{numbers[1]}"
        
        return value
    
    return None

def normalize_county_name(county_text):
    """Normalize county names with comprehensive OCR error handling"""
    if not county_text:
        return county_text
    
    county_text = county_text.upper().strip()
    
    county_text = re.sub(r'[^A-Z]', '', county_text)  
    
    county_lower = county_text.lower()
    
    normalized = get_valid_county(county_lower)
    

    return normalized.upper()

def process_ocr(document):
    """
    7. Process document OCR with database validation
    - Extracts data from document
    - Verifies against existing land records in database
    - Shows specific mismatches for user feedback
    """
    try:
        
        file_path = document.document_file_url
        if not default_storage.exists(file_path):
            raise Exception(f"Document file not found: {file_path}")

        file_content = default_storage.open(file_path).read()
        
        extracted_text = ""
        extracted_data = {}

        file_name = document.document_file_name.lower()
        
        if file_name.endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_content)
        elif file_name.endswith(('.jpg', '.jpeg', '.png')):
            extracted_text = extract_text_from_image(file_content)
        else:
            raise Exception("Unsupported file format. Please upload PDF or image files.")

        print(f"DEBUG: Extracted text length: {len(extracted_text)}")
        print(f"DEBUG: First 500 chars: {extracted_text[:500]}")
        
        extracted_data = extract_structured_data(extracted_text)

        print(f"DEBUG: Extracted data: {extracted_data}")
        
        document.document_ocr_text = extracted_text
        document.document_ocr_metadata = extracted_data
        
        if not extracted_data.get('parcel_number'):
            parcel_from_filename = extract_parcel_from_filename(document.document_file_name)
            if parcel_from_filename:
                extracted_data['parcel_number'] = parcel_from_filename
                document.document_ocr_metadata['parcel_number'] = parcel_from_filename
        
        parcel_number = extracted_data.get('parcel_number')
        deed_number = extracted_data.get('deed_number')
        owner_id = extracted_data.get('owner_id_number')
        
        validation_result = validate_document_against_database(
            parcel_number, 
            deed_number, 
            owner_id,
            extracted_data
        )
        
        
        land_record_linked = False
        if validation_result['is_valid'] and validation_result['land_record']:
            document.document_land_records_id = validation_result['land_record']
            land_record_linked = True


        if validation_result['is_valid']:
            document.document_status = 'verified'
            document.document_verification_notes = (
                f" Document automatically verified\n"
                f"{validation_result['match_summary']}"
            )
            
            verification_transaction = create_verification_transaction(document)
            
            if verification_transaction:
                print(" Created verification transaction")
                
        else:
            document.document_status = 'rejected'
            
            mismatch_details = ""
            if validation_result.get('specific_mismatches'):
                mismatch_details = "\n\n🔍 Specific Mismatches Found:\n"
                for mismatch in validation_result['specific_mismatches']:
                    mismatch_details += f"• {mismatch['message']}\n"
                    mismatch_details += f"  System: {mismatch['system_value']}\n"
                    mismatch_details += f"  Document: {mismatch['document_value']}\n\n"
            
            document.document_verification_notes = (
                f" Document verification FAILED\n"
                f"Reason: {validation_result['rejection_reason']}"
                f"{mismatch_details}"
                f"This document does not match our system records."
            )
            
            Notification.objects.create(
                notification_user_id=document.document_uploaded_by,
                notification_title='Document Verification Failed',
                notification_message=(
                    f'Document "{document.document_file_name}" failed verification. '
                    f'Reason: {validation_result["rejection_reason"]}'
                ),
                notification_type='error'
            )

        document.save()

        return {
            'success': True,
            'extracted_data': extracted_data,
            'linked_to_land_record': land_record_linked,
            'status': document.document_status,
            'validation_result': validation_result
        }
        
    except Exception as e:
        document.document_status = 'needs_review'
        document.document_verification_notes = f"OCR processing error: {str(e)}"
        document.save()
        raise e

# ==================== DATABASE VALIDATION ====================#
def validate_document_against_database(parcel_number, deed_number, owner_id, extracted_data):
    """8. Validate extracted data against database records"""
    from .models import LandRecord
    
    validation_result = {
        'is_valid': False,
        'land_record': None,
        'match_summary': 'No matching land record found',
        'rejection_reason': '',
        'specific_mismatches': [],
        'system_data': {},
        'document_data': {}
    }
    

    validation_result['document_data'] = {
        'parcel_number': parcel_number,
        'deed_number': deed_number,
        'owner_id': owner_id
    }
    

    if parcel_number:
        try:
            land_record = LandRecord.objects.get(land_records_parcel_number=parcel_number)
            validation_result['land_record'] = land_record
            

            validation_result['system_data'] = {
                'parcel_number': land_record.land_records_parcel_number,
                'deed_number': land_record.land_records_deed_number,
                'owner_id': land_record.land_records_owner_id.user_id_number if land_record.land_records_owner_id else None,
                'owner_name': land_record.land_records_owner_id.user_full_name if land_record.land_records_owner_id else None
            }
            

            has_mismatch = False
            

            if deed_number and land_record.land_records_deed_number:
                doc_deed = deed_number.replace(' ', '').upper()
                sys_deed = land_record.land_records_deed_number.replace(' ', '').upper()
                
                if doc_deed != sys_deed:
                    validation_result['specific_mismatches'].append({
                        'field': 'deed_number',
                        'system_value': land_record.land_records_deed_number,
                        'document_value': deed_number,
                        'message': f"Deed number doesn't match"
                    })
                    has_mismatch = True
            
            if owner_id and land_record.land_records_owner_id:
                if str(land_record.land_records_owner_id.user_id_number) != str(owner_id):
                    validation_result['specific_mismatches'].append({
                        'field': 'owner_id',
                        'system_value': land_record.land_records_owner_id.user_id_number,
                        'document_value': owner_id,
                        'message': f"Owner ID doesn't match"
                    })
                    has_mismatch = True
            
            if not has_mismatch:
                validation_result['is_valid'] = True
                validation_result['match_summary'] = f"Document verified for parcel {parcel_number}"
            else:
                validation_result['rejection_reason'] = "Data mismatch found"
                validation_result['match_summary'] = "Data doesn't match system records"
                
        except LandRecord.DoesNotExist:
            validation_result['rejection_reason'] = f"Parcel not found: {parcel_number}"
    
    else:
        validation_result['rejection_reason'] = "No parcel number found in document"
    
    return validation_result

# ==================== HELPER FUNCTIONS ====================#

def extract_parcel_from_filename(filename):
    """Extract parcel number from filename"""
    try:
        patterns = [
            r'deed_LR_([A-Z]+)_(\d+)_(\d+)',
            r'LR_([A-Z]+)_(\d+)_(\d+)',
            r'PARCEL_([A-Z0-9_]+)',
            r'LR([A-Z0-9/]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, filename, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"LR/{matches[0][0]}/{matches[0][1]}/{matches[0][2]}"
                else:
                    return matches[0]
        return None
    except Exception as e:
        print(f"Filename extraction error: {str(e)}")
        return None

def get_valid_county(possible_county):
    from .models import UserProfile
    
    actual_counties = [choice[0] for choice in UserProfile.COUNTY_CHOICES]
    
    possible_county = str(possible_county).lower().strip().replace(' ', '_')
    
    if possible_county in actual_counties:
        return possible_county
    
    variations = {
        # Coastal Region
        'mombasa': 'mombasa',
        'mombasaa': 'mombasa',
        'mombas': 'mombasa',
        'kwale': 'kwale',
        'kilifi': 'kilifi',
        'tana_river': 'tana_river',
        'tana': 'tana_river',
        'lamu': 'lamu',
        'taita_taveta': 'taita_taveta', 
        'taita': 'taita_taveta',
        'taitata': 'taita_taveta',
        'taitattaveta': 'taita_taveta',
        
        # North Eastern Region
        'garissa': 'garissa',
        'wajir': 'wajir',
        'mandera': 'mandera',
        'marsabit': 'marsabit',
        
        # Eastern Region
        'isiolo': 'isiolo',
        'isioloo': 'isiolo',
        'meru': 'meru',
        'tharaka_nithi': 'tharaka_nithi',
        'tharaka': 'tharaka_nithi',
        'tharak': 'tharaka_nithi',
        'embu': 'embu',
        'kitui': 'kitui',
        'machakos': 'machakos',
        'makueni': 'makueni',
        'makuen': 'makueni',
        
        # Central Region
        'nyandarua': 'nyandarua',
        'nyandaru': 'nyandarua',
        'nyeri': 'nyeri',
        'kirinyaga': 'kirinyaga',
        'kirinyag': 'kirinyaga',
        'muranga': 'muranga',
        'murang': 'muranga',
        'murangaa': 'muranga',
        'kiambu': 'kiambu',
        
        # Rift Valley Region
        'turkana': 'turkana',
        'west_pokot': 'west_pokot',
        'westpokot': 'west_pokot',
        'west': 'west_pokot',
        'samburu': 'samburu',
        'trans_nzoia': 'trans_nzoia',
        'transnzoia': 'trans_nzoia',
        'trans': 'trans_nzoia',
        'uasin_gishu': 'uasin_gishu',
        'uasingishu': 'uasin_gishu',
        'uasin': 'uasin_gishu',
        'elgeyo_marakwet': 'elgeyo_marakwet',
        'elgeyo': 'elgeyo_marakwet',
        'marakwet': 'elgeyo_marakwet',
        'nandi': 'nandi',
        'baringo': 'baringo',
        'laikipia': 'laikipia',
        'nakuru': 'nakuru',
        'narok': 'narok',
        'kajiado': 'kajiado',
        'kericho': 'kericho',
        'bomet': 'bomet',
        
        # Western Region
        'kakamega': 'kakamega',
        'kakameg': 'kakamega',
        'vihiga': 'vihiga',
        'bungoma': 'bungoma',
        'busia': 'busia',
        
        # Nyanza Region
        'siaya': 'siaya',
        'kisumu': 'kisumu',
        'kisumuu': 'kisumu',
        'kisum': 'kisumu',
        'homa_bay': 'homa_bay',
        'homabay': 'homa_bay',
        'homa': 'homa_bay',
        'migori': 'migori',
        'migorii': 'migori',
        'migorwu': 'migori',
        'migoru': 'migori',
        'migorov': 'migori', 
        'migorv': 'migori',
        'migor': 'migori',
        'kisii': 'kisii',
        'nyamira': 'nyamira',
        
        # Nairobi
        'nairobi': 'nairobi',
        'nairobii': 'nairobi',
        'nairob': 'nairobi',
    }
    
    if possible_county in variations:
        county_value = variations[possible_county]
        if county_value in actual_counties:
            return county_value
    
    for actual_county in actual_counties:
        if actual_county in possible_county or possible_county in actual_county:
            return actual_county
    
    return None

def extract_county_from_parcel(parcel_number):
    if not parcel_number:
        return None
    
    parcel_upper = parcel_number.upper()
    
    county_patterns = {
        'KISUMU': 'kisumu',
        'ISIOLO': 'isiolo',
        'NAIROBI': 'nairobi',
        'MOMBASA': 'mombasa',
        'KWALE': 'kwale',
        'KILIFI': 'kilifi',
        'TAITA': 'taita_taveta',
        'LAMU': 'lamu', 
        'TANA': 'tana_river',
        'GARISSA': 'garissa',
        'WAJIR': 'wajir',
        'MANDERA': 'mandera',
        'MARSABIT': 'marsabit',
        'MERU': 'meru',
        'THARAKA': 'tharaka_nithi',
        'EMBU': 'embu',
        'KITUI': 'kitui',
        'MACHAKOS': 'machakos',
        'MAKUENI': 'makueni',
        'NYANDARUA': 'nyandarua',
        'NYERI': 'nyeri',
        'KIRINYAGA': 'kirinyaga',
        'MURANGA': 'muranga',
        'KIAMBU': 'kiambu',
        'TURKANA': 'turkana',
        'WESTPOKOT': 'west_pokot',
        'SAMBURU': 'samburu',
        'TRANS': 'trans_nzoia',
        'UASIN': 'uasin_gishu',
        'ELGEYO': 'elgeyo_marakwet',
        'NANDI': 'nandi',
        'BARINGO': 'baringo',
        'LAIKIPIA': 'laikipia',
        'NAKURU': 'nakuru',
        'NAROK': 'narok',
        'KAJIADO': 'kajiado',
        'KERICHO': 'kericho',
        'BOMET': 'bomet',
        'KAKAMEGA': 'kakamega',
        'VIHIGA': 'vihiga',
        'BUNGOMA': 'bungoma',
        'BUSIA': 'busia',
        'SIAYA': 'siaya',
        'HOMA': 'homa_bay',
        'MIGORI': 'migori',
        'KISII': 'kisii',
        'NYAMIRA': 'nyamira',
    }
    
    for pattern, county_value in county_patterns.items():
        if pattern in parcel_upper:
            valid_county = get_valid_county(county_value)
            return valid_county
    
    filename_patterns = [
        r'LR_([A-Z]+)_',
        r'deed_LR_([A-Z]+)_',
        r'_LR_([A-Z]+)_',
        r'PARCEL_([A-Z]+)_',
    ]
    
    for pattern in filename_patterns:
        matches = re.findall(pattern, parcel_upper)
        if matches:
            county_abbr = matches[0]
            if county_abbr in county_patterns:
                valid_county = get_valid_county(county_patterns[county_abbr])
                return valid_county
    
    return None

# ==================== OTHER FUNCTIONS  ====================#

def assign_officers_by_county(land_record, transaction=None):
    """
    Automatically assign officers based on land record county
    Returns assigned officers or None if no officers found
    """
    if not land_record.land_records_county:
        return None

    county = land_record.land_records_county
    
    legal_officers = UserProfile.objects.filter(
        user_role='legal_officer',
        user_county=county,
        user_is_active=True
    )
    
    legal_officer = legal_officers.first() if legal_officers.exists() else None
    
    land_officers = UserProfile.objects.filter(
        user_role='land_officer',
        user_county=county,
        user_is_active=True
    )
    
    land_officer = land_officers.first() if land_officers.exists() else None
    
    if transaction:
        transaction.transaction_county = county
        transaction.transaction_legal_officer_id = legal_officer
        transaction.transaction_land_officer_id = land_officer
        transaction.save()
        
        if legal_officer:
            Notification.objects.create(
                notification_user_id=legal_officer,
                notification_title='New Transfer Assigned',
                notification_message=f'You have been assigned a transfer for {land_record.land_records_parcel_number} in {county} county.',
                notification_type='info'
            )
        
        if land_officer:
            Notification.objects.create(
                notification_user_id=land_officer,
                notification_title='New Transfer Assigned',
                notification_message=f'You have been assigned a transfer for {land_record.land_records_parcel_number} in {county} county.',
                notification_type='info'
            )
    
    return {
        'legal_officer': legal_officer,
        'land_officer': land_officer,
        'county': county
    }



def get_county_revenue_summary(county=None):
    """
    Get revenue summary for a specific county or all counties
    """
    from django.db.models import Sum, Count
    
    if county:
        transactions = Transaction.objects.filter(
            transaction_county=county,
            transaction_payment_status='completed'
        )
    else:
        transactions = Transaction.objects.filter(
            transaction_payment_status='completed'
        )
    
    total_revenue = transactions.aggregate(
        total_amount=Sum('transaction_amount'),
        total_transactions=Count('transaction_id')
    )
    
    legal_commissions = transactions.filter(
        transaction_legal_officer_id__isnull=False
    ).aggregate(total_legal=Sum('transaction_legal_officer_share'))
    
    land_commissions = transactions.filter(
        transaction_land_officer_id__isnull=False
    ).aggregate(total_land=Sum('transaction_land_officer_share'))
    
    return {
        'total_revenue': total_revenue['total_amount'] or 0,
        'total_transactions': total_revenue['total_transactions'] or 0,
        'legal_officer_commissions': legal_commissions['total_legal'] or 0,
        'land_officer_commissions': land_commissions['total_land'] or 0,
        'county': county or 'all'
    }


    
def create_missing_verification_transactions():
    """Create missing transactions for already verified documents"""
    try:
        from .models import Document, Transaction
        
        verified_docs = Document.objects.filter(
            document_status='verified',
            document_land_records_id__isnull=False
        )
        
        created_count = 0
        for doc in verified_docs:
            existing_transaction = Transaction.objects.filter(
                transaction_land_record_id=doc.document_land_records_id,
                transaction_type='verification'
            ).exists()
            
            if not existing_transaction:
                transaction = create_verification_transaction(doc)
                if transaction:
                    created_count += 1
        
        return {
            'success': True,
            'message': f'Created {created_count} missing verification transactions',
            'created_count': created_count,
            'total_verified': verified_docs.count()
        }
        
    except Exception as e:
        print(f"Error creating missing transactions: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_verification_transaction(document):
    try:
        from .models import Transaction, UserProfile, Notification
        from django.utils import timezone
        from decimal import Decimal
        
        
        if not document.document_land_records_id:
            return None
        
        land_record = document.document_land_records_id
        
        try:
            admin_user = UserProfile.objects.filter(user_role='admin').first()
            if not admin_user:
                admin_user = document.document_uploaded_by
        except:
            admin_user = document.document_uploaded_by
        
        transaction = Transaction.objects.create(
            transaction_land_record_id=land_record,  
            transaction_from_owner_id=document.document_uploaded_by,
            transaction_to_owner_id=land_record.land_records_owner_id,  
            transaction_type='verification',
            transaction_amount=Decimal('100.00'),
            transaction_payment_status='completed',
            transaction_payment_reference=f"DOC_VERIFY_{document.document_id}",
            transaction_legal_approval_status='approved',
            transaction_approved_at=timezone.now(),
            transaction_county=land_record.land_records_county,  
            transaction_legal_officer_share=Decimal('0.00'),  
            transaction_land_officer_share=Decimal('0.00'),   
            transaction_transfer_completed=True
        )
        
        

        Notification.objects.create(
            notification_user_id=document.document_uploaded_by,
            notification_title='Document Verification Complete',
            notification_message=f'Your document "{document.document_file_name}" for parcel {land_record.land_records_parcel_number} has been verified.',
            notification_type='success'
        )
        

        if admin_user and admin_user != document.document_uploaded_by:
            Notification.objects.create(
                notification_user_id=admin_user,
                notification_title='Document Verification Revenue',
                notification_message=f'KES 100 verification fee received for document "{document.document_file_name}".',
                notification_type='info'
            )
        
        return transaction
        
    except Exception as e:
        print(f"Error creating verification transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def create_land_record_from_ocr(extracted_data, uploaded_by):
    try:
        from .models import LandRecord, UserProfile
        
        parcel_number = extracted_data.get('parcel_number')
        if not parcel_number:
            return None
            
        county = extract_county_from_parcel(parcel_number)
        
        owner = uploaded_by
        owner_id_number = extracted_data.get('owner_id_number')
        if owner_id_number:
                owner = UserProfile.objects.get(user_id_number=owner_id_number)
 

        
        land_record = LandRecord.objects.create(
            land_records_parcel_number=parcel_number,
            land_records_deed_number=extracted_data.get('deed_number', f"DEED/{parcel_number}"),
            land_records_owner_id=owner,
            land_records_location=extracted_data.get('location', 'Unknown'),
            land_records_county=county,
            land_records_size=extracted_data.get('land_size', 0.0),
            land_records_verification_status='verified'
        )
        
        return land_record
        
    except Exception as e:
        print(f" Error creating land record: {str(e)}")
        return None

def manually_link_document_to_land_record(document, parcel_number):
    try:
        from .models import LandRecord
        land_record = LandRecord.objects.get(land_records_parcel_number=parcel_number)
        document.document_land_records_id = land_record
        document.save()
        
        if document.document_ocr_metadata:
            document.document_ocr_metadata['parcel_number'] = parcel_number
            document.save()
            
        return True
    except LandRecord.DoesNotExist:
        return False

def reprocess_ocr(document):
    try:
        document.document_status = 'processing'
        document.document_verification_notes = 'Reprocessing OCR...'
        document.save()
        
        return process_ocr(document)
    except Exception as e:
        document.document_status = 'needs_review'
        document.document_verification_notes = f"Reprocessing failed: {str(e)}"
        document.save()
        raise e

        
def get_mpesa_access_token():
    """
    Get M-Pesa API access token
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if not consumer_key or not consumer_secret:
        return None

    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        raise Exception(f"Failed to get M-Pesa access token: {str(e)}")


def initiate_mpesa_payment(phone_number, amount, description, user_profile, county=None):
    """
    Initiate M-Pesa STK Push payment with county tracking
    """
    if amount == 0:
        payment_reference = f"MPESA{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4]}"

        Notification.objects.create(
            notification_user_id=user_profile,
            notification_title='Payment Successful',
            notification_message=f'Your payment of {amount} KES has been processed successfully. Reference: {payment_reference}',
            notification_type='success'
        )

        return {
            'success': True,
            'message': 'Payment processed successfully (Demo Mode)',
            'payment_reference': payment_reference,
            'amount': amount,
            'phone_number': phone_number,
            'county': county,
            'status': 'completed',
            'timestamp': timezone.now().isoformat()
        }

    access_token = get_mpesa_access_token()
    if not access_token:
        raise Exception("M-Pesa credentials not configured")

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    if county:
        description = f"{description} - {county} County"

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": "TitleGuard",
        "TransactionDesc": description
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        return {
            'success': True,
            'message': 'Payment initiated successfully',
            'checkout_request_id': result.get('CheckoutRequestID'),
            'merchant_request_id': result.get('MerchantRequestID'),
            'response_code': result.get('ResponseCode'),
            'response_description': result.get('ResponseDescription'),
            'county': county
        }
    except Exception as e:
        raise Exception(f"M-Pesa payment initiation failed: {str(e)}")


def verify_document_authenticity(document):
    checks = {
        'ocr_completed': bool(document.document_ocr_text),
        'metadata_extracted': bool(document.document_ocr_metadata),
        'matches_land_record': False,
        'county_matches': False,
    }

    if document.document_land_records_id and document.document_ocr_metadata:
        metadata = document.document_ocr_metadata
        land_record = document.document_land_records_id

        parcel_match = metadata.get('parcel_number') == land_record.land_records_parcel_number
        deed_match = metadata.get('deed_number') == land_record.land_records_deed_number
        county_match = metadata.get('county') and metadata.get('county').lower() == land_record.land_records_county.lower()

        checks['matches_land_record'] = parcel_match and deed_match
        checks['county_matches'] = county_match

    return checks


def manually_correct_ocr_extraction(document, corrections):
    """
    Manually correct OCR extraction errors
    """
    try:
        if not document.document_ocr_metadata:
            document.document_ocr_metadata = {}
        
        for key, value in corrections.items():
            document.document_ocr_metadata[key] = value
        
        document.save()
        
        validation_result = validate_document_against_database(
            corrections.get('parcel_number'),
            corrections.get('deed_number'),
            corrections.get('owner_id_number'),
            document.document_ocr_metadata
        )
        
        return {
            'success': True,
            'message': 'Corrections applied',
            'validation_result': validation_result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }