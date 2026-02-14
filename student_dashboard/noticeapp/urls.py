from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/',views.admin_logout, name='admin_logout'),
    path('admin-dboard/', views.admin_dboard, name='admin_dboard'),
    path('add-admin/', views.add_admin, name='add_admin'),
    path('admin-list/',views.admin_list, name='admin_list'),
    path('edit-admin/<int:pk>/', views.edit_admin, name='edit_admin'),
    path('delete-admin/<int:pk>',views.delete_admin, name='delete_admin'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),

    path('add-department/', views.add_department, name='add_department'),
    path('department-list/', views.department_list, name='department_list'),
    path('delete-department/<int:pk>/', views.delete_department, name='delete_department'),
    path('update-department/<int:pk>/', views.update_department, name='update_department'),

    path('add-notice/', views.add_notice, name='add_notice'),
    path('notice_list/', views.notice_list, name='notice_list'),
    path('delete-notice/<int:pk>/', views.delete_notice, name='delete_notice'),
    path('update-notice/<int:pk>/', views.update_notice, name='update_notice'),

    path('add-student/', views.add_student, name='add_student'),
    path('update-student/<int:pk>/', views.update_student, name='update_student'),
    path('delete-student/<int:pk>/', views.delete_student, name='delete_student'),

    path('', views.student_dboard, name='student_dboard'),
    path('student-list/', views.student_list, name='student_list'),
    path('student-profile/',views.student_profile, name='student_profile'),
    path('student-login/',views.student_login, name='student_login'),
    path('student-logout/',views.student_logout, name='student_logout'),
    path('notice-detail/<int:pk>',views.student_detail, name='notice_detail')
]
