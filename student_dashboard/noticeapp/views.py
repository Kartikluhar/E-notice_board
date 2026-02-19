from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import AdminProfile, Department, Notice, Students
import re
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import csv

admin_validation = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
password_validation = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{7,}$'
email_validation = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# user defined functions here.

# Create your views here.

# ====================================================================================
# admin login, create admin, logout admin
# ====================================================================================


def admin_login(request):
    if request.user.is_authenticated:
        return redirect('notice_list')
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            role = user.profile.role
            if role.lower() == 'admin':
                login(request, user=user)
                return redirect('notice_list')
            else:
                messages.warning(request, "You are not allowed here!!")
        else:
            messages.warning(request, "Invalid credentials!!")

    return render(request, 'admin/admin_login.html')


@login_required(login_url='admin_login')
def admin_profile(request):
    return render(request, 'admin/admin_profile.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required(login_url='admin_login')
def add_admin(request):
    if request.method == 'POST':
        if 'single_admin' in request.POST:
            username = request.POST.get('username')
            first_name = request.POST.get('fname')
            last_name = request.POST.get('lname')
            email = request.POST.get('email')
            password = request.POST.get('password')

            if User.objects.filter(username=username).exists():
                messages.warning(
                    request, "User is already exist!!")
            elif not re.match(email_validation, email):
                messages.error(
                    request, "Enter valid email")
            elif not re.match(admin_validation, password):
                messages.error(
                    request, "password must contain 1 uppercase, 1 lowercase, 1 speacial character, and contain atleast 8 letter")
            elif username == "" or first_name == "" or last_name == "" or email == "" or password == "":
                messages.warning(request, "Field can not be empty!")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )
                messages.success(request, "Registered successfully!")
        else:
            try:
                csv_file = request.FILES.get('csv_file')
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, "Please Upload valid csv file")
                    return render(request, 'department/add_department.html')
                else:
                    decode_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.reader(decode_file)
                    next(reader)
                    admins = []
                    for row in reader:
                        admins.append(User(
                            username=row[0].strip(),
                            first_name=row[1].strip(),
                            last_name=row[2].strip(),
                            email=row[3].strip(),
                            password=row[4].strip(),
                            is_staff=True
                        ))
                    User.objects.bulk_create(admins, ignore_conflicts=True)
                    messages.success(
                        request, "Admins created successfully!")
                    return redirect('admin_list')
            except Exception as e:
                messages.error(request, f"Something went wrong {e}")
                return render(request, 'admin/add_admin.html')

    return render(request, 'admin/add_admin.html')


@login_required(login_url='admin_login')
def admin_dboard(request):
    notices = Notice.objects.select_related(
        'department').all().order_by('-created_at')

    # 🔍 Filters
    search = request.GET.get('search')
    department = request.GET.get('department')
    sem = request.GET.get('sem')
    status = request.GET.get('status')   # 👈 NEW

    if search:
        notices = notices.filter(notice_title__icontains=search)

    if department:
        notices = notices.filter(department_id=department)

    if sem:
        notices = notices.filter(sem=sem)

    now = timezone.now()
    if status == 'active':
        notices = notices.filter(expired_date__gt=now)
    elif status == 'expired':
        notices = notices.filter(expired_date__lte=now)

    lengths = {
        'notice_len': Notice.objects.count()
    }

    return render(request, 'notice/notice_list.html', {
        'notices': notices,
        'lengths': lengths,
        'now': timezone.now()
    })


@login_required(login_url='admin_login')
def admin_list(request):
    admins = User.objects.filter(is_staff=True)

    return render(request, 'admin/admin_list.html', {
        'admins': admins
    })


@login_required(login_url='admin_login')
def edit_admin(request, pk):
    admin = get_object_or_404(User, pk=pk, is_staff=True)

    # Prevent editing superuser (optional but recommended)
    if admin.is_superuser:
        messages.error(request, "Superuser cannot be edited.")
        return redirect('admin_list')

    if request.method == "POST":
        admin.first_name = request.POST.get('fname')
        admin.last_name = request.POST.get('lname')
        admin.email = request.POST.get('email')

        password = request.POST.get('password')
        if password:
            admin.set_password(password)

        admin.save()
        messages.success(request, "Admin updated successfully.")
        return redirect('admin_list')

    return render(request, 'admin/edit_admin.html', {
        'admin': admin
    })


@login_required(login_url='admin_login')
def delete_admin(request, pk):
    admin = get_object_or_404(User, pk=pk, is_staff=True)

    # Safety checks
    if admin.is_superuser:
        messages.error(request, "Superuser cannot be deleted.")
        return redirect('admin_list')

    if admin == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_list')

    admin.delete()
    messages.success(request, "Admin deleted successfully.")
    return redirect('admin_list')

# ====================================================================================
# create, update, delete department
# ====================================================================================


@login_required(login_url='admin_login')
def add_department(request):
    if request.method == 'POST':
        if 'single_student' in request.POST:
            department_name = request.POST.get('dept_name')
            department_code = request.POST.get('dept_code')

            if Department.objects.filter(d_code=department_code).exists():
                messages.error(
                    request, "Department is already exist! create new one")
            else:
                department = Department.objects.create(
                    d_name=department_name,
                    d_code=department_code
                )
                if department:
                    messages.success(
                        request, "Department is created Successfully.")
                else:
                    messages.error(request, "Something went wrong")
        else:
            try:
                csv_file = request.FILES.get('csv_file')
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, "Please Upload valid csv file")
                    return render(request, 'department/add_department.html')
                else:
                    decode_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.reader(decode_file)
                    next(reader)
                    departments = []
                    for row in reader:
                        departments.append(Department(
                            d_name=row[0].strip(),
                            d_code=row[1].strip()
                        ))
                    Department.objects.bulk_create(
                        departments, ignore_conflicts=True)
                    messages.success(
                        request, "Departments created successfully!")
            except Exception as e:
                messages.error(request, f"Something went wrong {e}")
                return render(request, 'department/add_department.html')

    return render(request, 'department/add_department.html')


@login_required(login_url='admin_login')
def department_list(request):
    d_list = Department.objects.all()
    return render(request, 'department/department_list.html', {
        'departments': d_list
    })


@login_required(login_url='admin_login')
def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    try:
        department.delete()
        messages.success(request, "Department Deleted Successfully!!")
    except Exception as e:
        print(e)
        messages.error(request, "Something went wrong!!")

    return redirect('department_list')


@login_required(login_url='admin_login')
def update_department(request, pk):
    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        try:
            department_name = request.POST.get('dept_name')
            department_code = request.POST.get('dept_code')

            department.d_name = department_name
            department.d_code = department_code
            department.save()

            messages.success(request, "Department updated successfully!")
            return redirect('department_list')

        except Exception as e:
            print(e)  # optional for debugging
            messages.error(request, "Something went wrong! Please try again.")

    return render(request, 'department/update_department.html', {
        'department': department
    })

@login_required(login_url='admin_login')
def delete_all_departments(request):
    Department.objects.all().delete()
    messages.success(request, "All departments deleted successfully!")
    return redirect('department_list')

# ====================================================================================
# create update delete notice
# ====================================================================================


@login_required(login_url='admin_login')
def add_notice(request):
    d_list = Department.objects.all()
    semesters = range(1, 13)
    if request.method == 'POST':
        try:

            notice_title = request.POST.get('title')
            notice_description = request.POST.get('description')
            notice_attachment = request.POST.get('attachment')
            department_id = request.POST.get('department')
            sem = request.POST.get('sem')
            expired_date_str = request.POST.get('expired_date')

            expired_date = parse_datetime(expired_date_str)

            dept = Department.objects.get(id=department_id)

            Notice.objects.create(
                notice_title=notice_title,
                notice_description=notice_description,
                department=dept,
                notice_attachment=notice_attachment,
                sem=sem,
                expired_date=expired_date
            )

            subject = "New Notice Published – College Portal"
            if sem == 'all':
                emails = Students.objects.filter(
                    department=dept
                ).values_list('email', flat=True)
                html_message = f"""
                <div style="font-family: Arial, sans-serif; background-color:#f4f6f9; padding:20px;">

                    <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1);">

                        <div style="text-align:center;">
                            <img src="https://ljku.edu.in/web/image/31899/FinalLJU1.png" width="80" />
                            <h2 style="color:#0d6efd; margin-top:10px;">📢 New Notice Published</h2>
                        </div>

                        <p style="font-size:16px;">Dear Student,</p>

                        <p style="font-size:15px; color:#555;">
                            We would like to inform you that a new notice has been published on the College Portal.
                        </p>

                        <div style="background:#f8f9fa; padding:15px; border-left:5px solid #0d6efd; margin:20px 0;">
                            <strong>Title:</strong> {notice_title}
                        </div>

                        <p style="font-size:15px;">
                            Please log in to the portal to view the complete details.
                        </p>

                        <div style="text-align:center; margin-top:25px;">
                            <a href="#" style="background:#0d6efd; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
                                View Notice
                            </a>
                        </div>

                        <hr style="margin-top:30px;">

                        <p style="font-size:14px; color:gray;">
                            Regards,<br>
                            <strong>College Administration</strong>
                        </p>

                    </div>
                </div>
                """
            else:
                emails = Students.objects.filter(
                    department=dept,
                    sem=sem
                ).values_list('email', flat=True)
                html_message = f"""
                <div style="font-family: Arial, sans-serif; background-color:#f4f6f9; padding:20px;">

                    <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1);">

                        <div style="text-align:center;">
                            <img src="https://ljku.edu.in/web/image/31899/FinalLJU1.png" width="80" />
                            <h2 style="color:#198754; margin-top:10px;">📢 Department Notice</h2>
                        </div>

                        <p style="font-size:16px;">Dear Student,</p>

                        <p style="font-size:15px; color:#555;">
                            A new notice has been published for your department on the College Portal.
                        </p>

                        <div style="background:#f8f9fa; padding:15px; border-left:5px solid #198754; margin:20px 0;">
                            <strong>Title:</strong> {notice_title}
                        </div>

                        <p style="font-size:15px;">
                            Please log in to the portal to view the complete details.
                        </p>

                        <div style="text-align:center; margin-top:25px;">
                            <a href="#" style="background:#198754; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
                                View Notice
                            </a>
                        </div>

                        <hr style="margin-top:30px;">

                        <p style="font-size:14px; color:gray;">
                            Regards,<br>
                            <strong>College Administration</strong>
                        </p>

                    </div>
                </div>
                """
            # send_mail(
            #     subject,
            #     message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     list(emails),
            #     fail_silently=True
            # )
            send_mail(
                subject,
                message="A new notice has been published.",  # fallback text
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(emails),
                html_message=html_message
            )

            messages.success(request, "Notice is created!!")

        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong! Please try again.")

    return render(request, 'notice/add_notice.html', {
        "departments": d_list,
        'semesters': semesters
    })


@login_required(login_url='admin_login')
def delete_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    try:
        notice.delete()
        messages.success(request, "Notice is Deleted Successfully!!")
    except Exception as e:
        print(e)
        messages.error(request, "Something went wrong! Can't delete Notice")

    return redirect('notice_list')

@login_required(login_url='admin_login')
def delete_all_notices(request):
    Notice.objects.all().delete()
    messages.success(request, "All notices deleted successfully!")
    return redirect('notice_list')

@login_required(login_url='admin_login')
def delete_expired_notices(request):
    Notice.objects.filter(expired_date__lte=timezone.now()).delete()
    messages.success(request, "All expired notices deleted successfully!")
    return redirect('notice_list')


@login_required(login_url='admin_login')
def update_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    semesters = range(1, 13)
    d_list = Department.objects.all()
    if request.method == 'POST':
        try:
            notice_title = request.POST.get('title')
            notice_description = request.POST.get('description')
            department_id = request.POST.get('department')
            notice_attachment = request.POST.get('attachment')
            sem = request.POST.get('sem')
            expired_date_str = request.POST.get('expired_date')
            expired_date = parse_datetime(expired_date_str)

            dept = Department.objects.get(id=department_id)

            notice.notice_title = notice_title
            notice.notice_description = notice_description
            notice.department = dept
            notice.notice_attachment = notice_attachment
            notice.sem = sem
            notice.expired_date = expired_date

            notice.save()

            subject = "Notice has been Updated – College Portal"
            if sem == 'all':
                emails = Students.objects.filter(
                    department=dept
                ).values_list('email', flat=True)
                html_message = f"""
                <div style="font-family: Arial, sans-serif; background-color:#f4f6f9; padding:20px;">
                    
                    <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1);">
                        
                        <div style="text-align:center;">
                            <img src="https://ljku.edu.in/web/image/31899/FinalLJU1.png" width="80" />
                            <h2 style="color:#dc3545; margin-top:10px;">✏️ Notice Updated</h2>
                        </div>

                        <p style="font-size:16px;">Dear Student,</p>

                        <p style="font-size:15px; color:#555;">
                            This is to inform you that an existing notice has been updated on the College Portal.
                        </p>

                        <div style="background:#fff3cd; padding:15px; border-left:5px solid #dc3545; margin:20px 0;">
                            <strong>Updated Notice Title:</strong> {notice_title}
                        </div>

                        <p style="font-size:15px;">
                            Kindly log in to the portal to check the latest information.
                        </p>

                        <div style="text-align:center; margin-top:25px;">
                            <a href="#" style="background:#dc3545; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
                                View Updated Notice
                            </a>
                        </div>

                        <hr style="margin-top:30px;">

                        <p style="font-size:14px; color:gray;">
                            Regards,<br>
                            <strong>College Administration</strong>
                        </p>

                    </div>
                </div>
                """
            else:
                emails = Students.objects.filter(
                    department=dept,
                    sem=sem
                ).values_list('email', flat=True)
                html_message = f"""
                <div style="font-family: Arial, sans-serif; background-color:#f4f6f9; padding:20px;">
                    
                    <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1);">
                        
                        <div style="text-align:center;">
                            <img src="https://ljku.edu.in/web/image/31899/FinalLJU1.png" width="80" />
                            <h2 style="color:#198754; margin-top:10px;">✏️ Department Notice Updated</h2>
                        </div>

                        <p style="font-size:16px;">Dear Student,</p>

                        <p style="font-size:15px; color:#555;">
                            An existing notice for your department has been updated on the College Portal.
                        </p>

                        <div style="background:#e9f7ef; padding:15px; border-left:5px solid #198754; margin:20px 0;">
                            <strong>Updated Notice Title:</strong> {notice_title}
                        </div>

                        <p style="font-size:15px;">
                            Kindly log in to the portal to check the latest information.
                        </p>

                        <div style="text-align:center; margin-top:25px;">
                            <a href="#" style="background:#198754; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
                                View Updated Notice
                            </a>
                        </div>

                        <hr style="margin-top:30px;">

                        <p style="font-size:14px; color:gray;">
                            Regards,<br>
                            <strong>College Administration</strong>
                        </p>

                    </div>
                </div>
                """
            send_mail(
                subject,
                message="A new notice has been published.",  # fallback text
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(emails),
                html_message=html_message
            )

            messages.success(request, "Department updated successfully!")

            return redirect('notice_list')
        except Exception as e:
            print(e)
            messages.error(
                request, "Something went wrong! Can't Update Notice")
    return render(request, 'notice/update_notice.html', {
        'departments': d_list,
        'notice': notice,
        'semesters': semesters
    })


@login_required(login_url='admin_login')
def notice_list(request):
    notices = Notice.objects.select_related(
        'department').all().order_by('-created_at')

    # 🔍 Filters
    search = request.GET.get('search')
    department = request.GET.get('department')
    sem = request.GET.get('sem')
    status = request.GET.get('status')   # 👈 NEW

    if search:
        notices = notices.filter(notice_title__icontains=search)

    if department:
        notices = notices.filter(department_id=department)

    if sem:
        notices = notices.filter(sem=sem)

    now = timezone.now()
    if status == 'active':
        notices = notices.filter(expired_date__gt=now)
    elif status == 'expired':
        notices = notices.filter(expired_date__lte=now)

    lengths = {
        'notice_len': Notice.objects.count()
    }

    return render(request, 'notice/notice_list.html', {
        'notices': notices,
        'lengths': lengths,
        'now': timezone.now()
    })
# ====================================================================================
# create, update, delete student
# ====================================================================================


@login_required(login_url='admin_login')
def add_student(request):
    d_list = Department.objects.all()
    semesters = range(1, 13)

    if request.method == "POST":
        if 'single_student' in request.POST:
            try:
                enrollment_no = request.POST.get('enrollment_no')
                email = request.POST.get('email')
                full_name = request.POST.get('full_name')
                password = request.POST.get('password')
                department_id = request.POST.get('department')
                sem = request.POST.get('sem')

                if Students.objects.filter(enrollment_no=enrollment_no).exists():
                    messages.error(
                        request, "Student already exist with this enrollment no !!")

                elif not re.match(password_validation, password):
                    messages.error(
                        request,
                        "Password must contain 1 uppercase, 1 lowercase, 1 number, 1 special character and minimum 7 characters."
                    )

                elif enrollment_no == "" or full_name == "" or email == "" or password == "":
                    messages.error(request, "Fields cannot be empty!")

                else:

                    dept = Department.objects.get(id=department_id)
                    create_student = Students.objects.create(
                        enrollment_no=enrollment_no,
                        full_name=full_name,
                        email=email,
                        department=dept,
                        password=make_password(password),
                        sem=sem
                    )

                    if create_student:
                        messages.success(
                            request, "Student created successfully!!")
                    else:
                        messages.error(request, "Something went wrong!!")

            except Exception as e:
                print(e)
                messages.error(
                    request, f"Something went wrong! can't add Student {e}")
        else:
            try:
                csv_file = request.FILES.get('csv_file')
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, "Please Upload valid csv file")
                    return render(request, 'department/add_department.html')
                else:
                    decode_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.reader(decode_file)
                    next(reader)
                    students = []
                    for row in reader:
                        dept = Department.objects.get(d_code=row[4])
                        students.append(Students(
                            enrollment_no=row[0].strip(),
                            email=row[1].strip(),
                            full_name=row[2].strip(),
                            password=make_password(row[3].strip()),
                            department=dept,
                            sem=row[5]
                        ))
                    Students.objects.bulk_create(
                        students, ignore_conflicts=True)
                    messages.success(
                        request, "Students created successfully!")
            except Exception as e:
                messages.error(request, f"Something went wrong {e}")
                return render(request, 'admin/admin_create_student.html')

    return render(request, 'admin/admin_create_student.html', {
        'departments': d_list,
        'semesters': semesters
    })


@login_required(login_url='admin_login')
def update_student(request, pk):
    d_list = Department.objects.all()
    semesters = range(1, 13)

    student = get_object_or_404(Students, pk=pk)
    if request.method == "POST":
        try:
            enrollment_no = request.POST.get('enrollment_no')
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            department_id = request.POST.get('department')

            dept = Department.objects.get(id=department_id)
            sem = request.POST.get('sem')

            student.enrollment_no = enrollment_no
            if password:
                if not re.match(password_validation, password):
                    messages.error(
                        request,
                        "Password must contain 1 uppercase, 1 lowercase, 1 number, 1 special character and minimum 7 characters."
                    )
                    return redirect('update_student', pk=pk)

                student.password = make_password(password)

            student.full_name = full_name
            student.email = email
            student.department = dept
            student.sem = sem

            student.save()

            messages.success(request, "Student Updated successfully!!")

            return redirect('student_list')

        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong! can't add Student")

    return render(request, 'admin/admin_update_student.html', {
        'departments': d_list,
        'student': student,
        'semesters': semesters
    })


@login_required(login_url='admin_login')
def delete_student(request, pk):
    student = get_object_or_404(Students, pk=pk)
    try:
        student.delete()
        messages.success(request, "Student is Deleted Successfully!!")
    except Exception as e:
        print(e)
        messages.error(request, "Something went wrong! Can't delete Notice")

    return redirect('student_list')

@login_required(login_url='admin_login')
def delete_all_students(request):
    Students.objects.all().delete()
    messages.success(request, "All students deleted successfully!")
    return redirect('student_list')


@login_required(login_url='admin_login')
def student_list(request):
    students = Students.objects.all()
    departments = Department.objects.all()
    student_count = students.count()

    search = request.GET.get('search')
    department = request.GET.get('department')
    sem = request.GET.get('sem')

    if search:
        students = students.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(enrollment_no__icontains=search)
        )

    if department:
        students = students.filter(department_id=department)

    if sem:
        students = students.filter(sem=sem)

    context = {
        'students': students,
        'departments': departments,
        'total_students': student_count
    }

    return render(request, 'admin/admin_list_student.html', context)


# ====================================================================================
# this is all for student
# ====================================================================================

# student login using enrollment no and password and all data stored in Student model
def student_login(request):
    if 'student' in request.session:
        return redirect('student_dboard')

    if request.method == 'POST':
        enrollment_no = request.POST.get('enrollment_no')
        password = request.POST.get('password')

        try:
            student = Students.objects.get(enrollment_no=enrollment_no)

            if check_password(password, student.password):
                request.session['student'] = student.id
                request.session['is_student_logged_in'] = True
                messages.success(request, "Logged in successfully!")
                return redirect('student_dboard')
            else:
                messages.error(request, "Wrong password!")

        except Students.DoesNotExist:
            messages.error(request, "Invalid enrollment number!")

    return render(request, 'student/student_login.html')


def student_dboard(request):
    if 'student' in request.session:
        student = get_object_or_404(Students, pk=request.session['student'])
        now = timezone.now()

        semester_notices = Notice.objects.filter(
            department=student.department,
            sem=student.sem,
            expired_date__gt=now,
            is_active=True
        ).order_by('-created_at')

        common_notices = Notice.objects.filter(
            department=student.department,
            sem='all',
            expired_date__gt=now,
            is_active=True
        ).order_by('-created_at')

        return render(request, 'student/student_dboard.html', {
            'student': student,
            'semester_notices': semester_notices,
            'total_notices': (semester_notices.count() + common_notices.count()),
            'common_notices': common_notices
        })
    else:
        return redirect('student_login')


def student_profile(request):
    if 'student' in request.session:
        student = get_object_or_404(Students, pk=request.session['student'])
    else:
        return redirect('student_login')
    return render(request, 'student/student_profile.html', {'student': student})


def student_logout(request):
    request.session.flush()
    return redirect('student_login')


def student_detail(request, pk):
    if 'student' in request.session:
        try:
            # student = Students.objects.get(id=request.session['student'])
            notice = get_object_or_404(Notice, pk=pk)
            return render(request, 'student/student_detail.html', {
                'notice': notice
            })
        except Exception as e:
            print(e)
            messages.error("Something went wrong! Please try again")
    else:
        messages.warning(request, "Session has expired! Please login again")
        return redirect('student_login')
