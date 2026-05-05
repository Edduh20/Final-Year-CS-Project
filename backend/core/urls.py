from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views
from .views import AdminAddMinimalUsersView

router = DefaultRouter()
router.register(r'users', views.UserProfileViewSet, basename='user')
router.register(r'land-records', views.LandRecordViewSet, basename='land-record')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('land-records/download-report/', views.download_land_records_report, name='land-record-download-report'),
    path('', include(router.urls)),
    path('auth/register/', auth_views.register_user, name='auth-register'),
    path('auth/create-officer/', auth_views.create_officer, name='auth-create-officer'),
    path('auth/verify-otp/', auth_views.verify_otp, name='auth-verify-otp'),
    path('auth/resend-otp/', auth_views.resend_otp, name='auth-resend-otp'),
    path('auth/login/', auth_views.login_user, name='auth-login'),
    path('auth/logout/', auth_views.logout_user, name='auth-logout'),
    path('auth/me/', auth_views.current_user, name='auth-me'),
    path('auth/complete-first-login/', auth_views.complete_first_login, name='auth-complete-first-login'),
    path('auth/change-password/', auth_views.change_password, name='auth-change-password'),
    path('transfers/initiate/', views.initiate_transfer, name='transfer-initiate'),
    path('transfers/accept/<str:token>/', views.accept_transfer, name='transfer-accept'),
    path('transfers/<uuid:transaction_id>/approve/', views.approve_transfer, name='transfer-approve'),
    path('transfers/flag-land/', views.flag_land_for_case, name='transfer-flag-land'),
    path('transfers/unflag-land/', views.unflag_land, name='transfer-unflag-land'),
    path('transfers/my-commissions/', views.my_commissions, name='transfer-my-commissions'),
    path('verification-requests/create/', views.request_land_verification, name='verification-request-create'),
    path('dashboard/statistics/', views.dashboard_statistics, name='dashboard-statistics'),
    path('ocr/process/', views.process_ocr_endpoint, name='ocr-process'),
    path('payments/initiate-transfer/', views.initiate_transfer_payment, name='initiate_transfer_payment'),
    path('payments/mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('payments/check-status/<str:checkout_id>/', views.check_transaction_status, name='check_transaction_status'),
    path('documents/<uuid:document_id>/download/', views.download_document, name='document-download'),
    path('transactions/<uuid:transaction_id>/download/', views.download_transaction_receipt, name='transaction-download'),
    path('transactions/my-report/download/', views.download_my_transactions, name='my-transactions-download'),
    path('land-records/<uuid:land_record_id>/download-deed/', views.download_land_deed, name='land-record-download-deed'),
    path('reports/users/', views.download_user_report, name='user-download-report'),
    path('reports/commissions/', views.download_commissions_report, name='commission-download-report'),
    path('reports/transactions/', views.download_transactions_report, name='transaction-download-report'),
    path('land-records/search/', views.search_land_records, name='land-records-search'),
    path('legal-cases/submit/', views.submit_legal_case, name='submit-legal-case'),
    path('legal-cases/', views.get_legal_cases, name='get-legal-cases'),
    path('legal-cases/<uuid:case_id>/update-status/', views.update_case_status, name='update-case-status'),
    path('land-records/<uuid:land_record_id>/ownership-history/', views.get_ownership_history, name='land-record-ownership-history'),
    path('debug/transactions/all/', views.debug_all_transactions, name='debug-all-transactions'),
    path('revenue/county/', views.county_revenue, name='county-revenue'),
    path('reports/legal-cases/', views.download_legal_cases_report, name='legal-cases-download-report'),
    path('payments/initiate-verification/', views.initiate_verification_payment, name='initiate_verification_payment'),
    path('verification/delete/<uuid:document_id>/', views.delete_verification, name='delete_verification'),
    path('users/admin/add-minimal/', AdminAddMinimalUsersView.as_view(), name='admin-add-minimal-users'),
    
]