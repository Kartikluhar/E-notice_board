from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import AdminProfile, Department, Notice, Students
import re

password_validation = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
email_validation = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# user defined functions here.

# Create your views here.

# ====================================================================================
# admin login, create admin, logout admin
# ====================================================================================


def admin_login(request):
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            role = user.profile.role
            if role.lower() == 'admin':
                login(request, user=user)
                return redirect('admin_dboard')
            else:
                messages.warning(request, "You are not allowed here!!")
        else:
            messages.warning(request, "Invalid credentials!!")

    return render(request, 'admin/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required(login_url='admin_login')
def add_admin(request):
    if request.method == 'POST':

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
        elif not re.match(password_validation, password):
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

    return render(request, 'admin/add_admin.html')


@login_required(login_url='admin_login')
def admin_dboard(request):
    notice = Notice.objects.all()
    students = Students.objects.all()
    departments = Department.objects.all()

    lengths = {
        'notice_len': len(notice),
        'student_len': len(students),
        'department_len': len(departments)
    }

    return render(request, 'admin/admin_dboard.html', {
        'notices': notice,
        'lengths': lengths
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

            dept = Department.objects.get(id=department_id)

            Notice.objects.create(
                notice_title=notice_title,
                notice_description=notice_description,
                department=dept,
                notice_attachment=notice_attachment,
                sem=sem
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

    return redirect('admin_dboard')


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

            dept = Department.objects.get(id=department_id)

            notice.notice_title = notice_title
            notice.notice_description = notice_description
            notice.department = dept
            notice.notice_attachment = notice_attachment
            notice.sem = sem

            notice.save()

            messages.success(request, "Department updated successfully!")

            return redirect('admin_dboard')
        except Exception as e:
            print(e)
            messages.error(
                request, "Something went wrong! Can't Update Notice")
    return render(request, 'notice/update_notice.html', {
        'departments': d_list,
        'notice': notice,
        'semesters': semesters
    })

# ====================================================================================
# create, update, delete student
# ====================================================================================


@login_required(login_url='admin_login')
def add_student(request):
    d_list = Department.objects.all()
    semesters = range(1, 13)

    if request.method == "POST":
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
                    messages.success(request, "Student created successfully!!")
                else:
                    messages.error(request, "Something went wrong!!")

        except Exception as e:
            print(e)
            messages.error(
                request, f"Something went wrong! can't add Student {e}")

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
            student.password = make_password(password=password)
            student.full_name = full_name
            student.email = email
            student.department = dept
            student.sem = sem

            student.save()

            messages.success(request, "Student Updated successfully!!")

            return redirect('admin_dboard')

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
def student_list(request):
    s_list = Students.objects.all()

    s_list_ds = []

    return render(request, 'admin/admin_list_student.html', {
        'students': s_list
    })


# ====================================================================================
# this is all for student
# ====================================================================================

# student login using enrollment no and password and all data stored in Student model
def student_login(request):
    if request.method == 'POST':
        try:
            enrollment_no = request.POST.get('enrollment_no')
            password = request.POST.get('password')
            student = Students.objects.get(enrollment_no=enrollment_no)
            student_pass = student.password
            if student:
                if check_password(password=password, encoded=student_pass):
                    request.session['student'] = student.id
                    request.session['is_student_logged_in'] = True
                    messages.success(request, "Logged in successfully!")
                    return redirect('student_dboard')
                else:
                    messages.warning(request, "Enter correct password!")
            else:
                messages.error(
                    request, "Student not found enter correct enrollment.")
        except Exception as e:
            print(e)
    return render(request, 'student/student_login.html')


def student_dboard(request):
    if 'student' in request.session:
        # student = Students.objects.get(id=request.session['student'])
        student = get_object_or_404(Students, pk=request.session['student'])
        semester_notices = Notice.objects.filter(
            department=student.department, sem=student.sem)
        common_notices = Notice.objects.filter(
            department=student.department, sem='all')

        return render(request, 'student/student_dboard.html', {
            'student': student,
            'semester_notices': semester_notices,
            'total_notices': (len(semester_notices) + len(common_notices)),
            'common_notices': common_notices
        })
    else:
        messages.warning(request, "Session has expired! Please login again")
        return redirect('student_login')


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
