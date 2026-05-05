from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import UserProfile, Notification
from .serializers import UserProfileSerializer
import secrets



@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('full_name')
    id_number = request.data.get('id_number')
    phone_number = request.data.get('phone_number')

    if not email or not password or not full_name or not id_number:
        return Response(
            {'error': 'Email, password, full name, and ID number are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    
    if UserProfile.objects.filter(user_email=email).exists():
        return Response(
            {'error': 'User with this email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    
    existing_user = UserProfile.objects.filter(user_id_number=id_number).first()
    if existing_user:
        if not getattr(existing_user, "user_is_registered", True):
            existing_user.user_email = email
            existing_user.set_password(password)
            existing_user.user_full_name = full_name
            existing_user.user_phone_number = phone_number
            existing_user.user_role = "user"
            existing_user.user_email_verified = True
            existing_user.user_first_login_completed = False
            existing_user.user_is_registered = True
            existing_user.save()

            
            Notification.objects.create(
                notification_user_id=existing_user,
                notification_title="Registration Completed",
                notification_message="Your placeholder record has been activated into a full account.",
                notification_type="success"
            )

            
            refresh = RefreshToken.for_user(existing_user)
            serializer = UserProfileSerializer(existing_user)
            return Response(
                {
                    "message": "User upgraded successfully",
                    "user": serializer.data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {'error': 'User with this ID number already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )


    try:
        user = UserProfile.objects.create_user(
            user_email=email,
            password=password,
            user_full_name=full_name,
            user_role='user',
            user_phone_number=phone_number,
            user_id_number=id_number,
            user_email_verified=True,
            user_first_login_completed=False,
            user_is_registered=True  
        )

       
        Notification.objects.create(
            notification_user_id=user,
            notification_title='Welcome to TitleGuard!',
            notification_message='Your account has been created successfully. You can now manage your land records.',
            notification_type='success'
        )

   
        refresh = RefreshToken.for_user(user)
        serializer = UserProfileSerializer(user)

        return Response(
            {
                'message': 'User registered successfully',
                'user': serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_officer(request):
    if request.user.user_role not in ['admin', 'superadmin']:
        return Response({'error': 'Only admins can create officers'}, status=status.HTTP_403_FORBIDDEN)

    email = request.data.get('email')
    full_name = request.data.get('full_name')
    role = request.data.get('role')
    phone_number = request.data.get('phone_number')
    id_number = request.data.get('id_number')
    county = request.data.get('county')

    if role not in ['land_officer', 'legal_officer']:
        return Response({'error': 'Invalid role. Must be land_officer or legal_officer'}, status=status.HTTP_400_BAD_REQUEST)

    if not email or not full_name:
        return Response({'error': 'Email and full name are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not county:
        return Response({'error': 'County is required for officers'}, status=status.HTTP_400_BAD_REQUEST)

    if UserProfile.objects.filter(user_email=email).exists():
        return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        temp_password = secrets.token_urlsafe(12)
        user = UserProfile.objects.create_user(
            user_email=email,
            password=temp_password,
            user_full_name=full_name,
            user_role=role,
            user_phone_number=phone_number,
            user_id_number=id_number,
            user_county=county,
            user_email_verified=False,
            user_first_login_completed=False
        )

       
        user.generate_otp(temp_password=temp_password)

        Notification.objects.create(
            notification_user_id=request.user,  
            notification_title='Officer Account Created', 
            notification_message=f'{role.replace("_", " ").title()} account created for {full_name}. OTP sent to {email}.',  
            notification_type='success' 
        )

        Notification.objects.create(
            notification_user_id=user,  
            notification_title='Welcome to TitleGuard',  
            notification_message=f'Your {role.replace("_", " ")} account has been created for {county} county. Please check your email for the OTP.',  
            notification_type='info'  
        )
        
        serializer = UserProfileSerializer(user)
        return Response(
            {
                'message': 'Officer created successfully. OTP sent to email.',
                'user': serializer.data,
                'temporary_password': temp_password
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    
    if not email or not otp:
        return Response(
            {'error': 'Email and OTP are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = UserProfile.objects.get(user_email=email)
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if user.verify_otp(otp):
        if user.user_role in ['land_officer', 'legal_officer'] and not user.user_first_login_completed:
            user.user_first_login_completed = True
            user.save()
        
        Notification.objects.create(
            notification_user_id=user,
            notification_title='Email Verified Successfully',
            notification_message='Your email has been verified successfully. You can now log in.',
            notification_type='success'
        )
        
        return Response({
            'message': 'Email verified successfully! You can now log in.',
            'user': {
                'name': user.user_full_name,
                'email': user.user_email,
                'role': user.user_role,
                'first_login_completed': user.user_first_login_completed
            }
        })
    else:
        return Response(
            {'error': 'Invalid or expired OTP'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = UserProfile.objects.get(user_email=email)
    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if user.user_email_verified:
        return Response({'error': 'Email is already verified'}, status=status.HTTP_400_BAD_REQUEST)

    user.generate_otp()
    return Response({'message': 'OTP has been resent to your email'})



@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(user_email=email, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.user_is_active:
        return Response({'error': 'User account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)

    if user.user_role in ['land_officer', 'legal_officer'] and not user.user_email_verified:
        return Response(
            {
                'error': 'Email not verified',
                'message': 'Please verify your email with the OTP sent to you before logging in.',
                'requires_otp': True
            },
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)
    serializer = UserProfileSerializer(user)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': serializer.data,
        'first_login': not user.user_first_login_completed
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_first_login(request):
    user = request.user

    if user.user_first_login_completed:
        return Response({'error': 'First login already completed'}, status=status.HTTP_400_BAD_REQUEST)

    phone_number = request.data.get('phone_number')
    id_number = request.data.get('id_number')
    new_password = request.data.get('new_password')

    if phone_number:
        user.user_phone_number = phone_number
    if id_number:
        user.user_id_number = id_number
    if new_password:
        user.set_password(new_password)

    user.user_first_login_completed = True
    user.save()

    Notification.objects.create(
        notification_user_id=user,  
        notification_title='Profile Setup Complete', 
        notification_message='Your profile has been successfully set up. Welcome to TitleGuard!',  
    )

    serializer = UserProfileSerializer(user)
    return Response({'message': 'Profile updated successfully', 'user': serializer.data})



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    return Response({'message': 'Logged out successfully'})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response({'error': 'Old and new passwords are required'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response({'error': 'Incorrect old password'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    Notification.objects.create(
        notification_user_id=user,  
        notification_title='Password Changed', 
        notification_message='Your password has been changed successfully.',  
        notification_type='success'  
    )

    return Response({'message': 'Password changed successfully'})